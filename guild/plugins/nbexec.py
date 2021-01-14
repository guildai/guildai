# Copyright 2017-2020 TensorHub, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division

import argparse
import ast
import base64
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import token
import tokenize

import six

from guild import op_util
from guild import run as runlib
from guild import util

from . import ipynb

log = None  # initialized in _init_logging


class ApplyFlagsState(object):
    def __init__(self, notebook_path, flags, run):
        self.notebook_path = notebook_path
        self.flags = flags
        op_data = run.get("op", {})
        self.flags_extra = op_data.get("flags-extra")


def main():
    _init_logging()
    args, rest_args = _parse_args()
    run = _init_run(args)
    _check_env()
    flags, other_args = op_util.args_to_flags(rest_args)
    if other_args:
        log.warning(
            "unexpected args: %s",
            " ".join([util.shlex_quote(arg) for arg in other_args]),
        )
    run_notebook = _init_run_notebook(args.notebook, flags, run)
    if args.no_exec or os.getenv("NB_NO_EXEC") == "1":
        log.info("NB_NO_EXEC specified, skipping execute")
        return
    _nbexec(run_notebook)
    _print_output(run_notebook)
    _save_images(run_notebook)
    _nbconvert_html(run_notebook)


def _init_logging():
    op_util.init_logging(logging.INFO)
    globals()["log"] = logging.getLogger("guild")


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("notebook")
    p.add_argument("--run-dir")
    p.add_argument("--no-exec", action="store_true")
    return p.parse_known_args()


def _init_run(args):
    if args.run_dir:
        return runlib.for_dir(args.run_dir)
    return op_util.current_run()


def _check_env():
    _check_nbconvert()
    _check_nbextensions()


def _init_flags(run, args):
    arg_flags, other_args = op_util.args_to_flags(args)
    if other_args:
        log.warning(
            "unexpected args: %s",
            " ".join([util.shlex_quote(arg) for arg in other_args]),
        )
    flags = run.get("flags", {})
    flags.update(arg_flags)
    return flags


def _check_nbconvert():
    nbconvert = util.which("jupyter-nbconvert")
    if not nbconvert:
        log.error(
            "jupyter-nbconvert is required to run Notebooks - "
            "install it by running 'pip install jupyter' and try again"
        )
        sys.exit(1)


def _check_nbextensions():
    try:
        import jupyter_contrib_nbextensions as _
    except ImportError:
        log.error(
            "jupyter_contrib_nbextensions is required to run Notebooks - "
            "install it by running 'pip install jupyter_contrib_nbextensions' "
            "and try again"
        )
        sys.exit(1)


def _nbexec(notebook):
    notebook_relpath = _relpath(notebook)
    cmd = [
        "jupyter-nbconvert",
        "-y",
        "--log-level",
        "WARN",
        "--to",
        "notebook",
        "--execute",
        "--inplace",
        notebook_relpath,
    ]
    log.debug("jupyter-nbconvert cmd: %s", cmd)
    log.info("Executing %s", notebook_relpath)
    returncode = subprocess.call(cmd)
    if returncode != 0:
        sys.exit(returncode)


def _relpath(path):
    return os.path.relpath(os.path.realpath(path))


def _init_run_notebook(notebook, flags, run):
    src = _find_notebook(notebook)
    basename = os.path.basename(src)
    dest = os.path.join(run.dir, basename)
    log.info("Initializing %s for run", basename)
    shutil.copyfile(src, dest)
    _apply_flags_to_notebook(ApplyFlagsState(dest, flags, run))
    return dest


def _find_notebook(notebook):
    for path in sys.path:
        maybe_notebook = os.path.join(path, notebook)
        if os.path.exists(maybe_notebook):
            return maybe_notebook
    log.error(
        "cannot find notebook '%s' - make sure it's copied as source code\n"
        "Use 'guild run <operation> --test-sourcecode to troubleshoot source code "
        "configuration issues" % notebook
    )
    sys.exit(1)


def _apply_flags_to_notebook(state):
    nb_data = json.load(open(state.notebook_path))
    for cell in nb_data.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        _apply_flags_to_code_source(cell, state)
    json.dump(nb_data, open(state.notebook_path, "w"))


def _apply_flags_to_code_source(cell, state):
    source_lines = cell["source"]
    repl_source_lines = _apply_flags_to_source_lines(source_lines, state)
    cell["source"] = repl_source_lines


def _apply_flags_to_source_lines(source_lines, state):
    source = "".join(source_lines)
    source = ipynb._ipython_to_python(source)
    source = _replace_flag_pattern_vals(source, state)
    source = _replace_flag_assign_vals(source, state)
    return io.StringIO(source).readlines()


def _replace_flag_pattern_vals(source, state):
    for val, config in _iter_flag_replace_config(state.flags, state.flags_extra):
        for pattern in config:
            source = _replace_flag_ref(pattern, val, source)
    return source


def _iter_flag_replace_config(flags, flags_extra):
    for name, extra in sorted(flags_extra.items()):
        try:
            config = extra["nb-replace"]
            val = flags[name]
        except KeyError:
            pass
        else:
            yield val, _coerce_repl_config_to_list(config)


def _coerce_repl_config_to_list(config):
    if isinstance(config, six.string_types):
        return [config]
    elif isinstance(config, list):
        return config
    else:
        log.warning("unsupported nb-replace %r, ignoring", config)
        return []


def _replace_flag_ref(pattern, val, s):
    try:
        m = re.search(pattern, s, re.MULTILINE)
    except ValueError:
        return s
    else:
        if not m:
            return s
        return _apply_flag_to_repl_match(val, m, s)


def _apply_flag_to_repl_match(val, m, s):
    formatted_val = repr(val)
    parts = []
    cur = 0
    for slice_start, slice_end in _pattern_slices(m):
        parts.append(s[cur:slice_start])
        parts.append(formatted_val)
        cur = slice_end
    parts.append(s[cur:])
    return "".join(parts)


def _pattern_slices(m):
    if len(m.regs) == 1:
        # No replacement groups so assume entire match is replaced.
        return m.regs
    else:
        # Only use explicit replacement groups.
        return m.regs[1:]


def _replace_flag_assign_vals(source, state):
    assigns = _assigns_lookup_for_source(source, state.flags)
    source_tokens = _tokenize_source(source)
    repl_tokens = _replace_assigns_for_tokens(source_tokens, assigns)
    return tokenize.untokenize(repl_tokens)


def _assigns_lookup_for_source(source, flags):
    assigns = _assigns_for_source(source, flags)
    return {
        (target_node.id, (target_node.lineno, target_node.col_offset)): (
            target_node,
            val_node,
            flag_val,
        )
        for target_node, val_node, flag_val in assigns
    }


def _assigns_for_source(source, flags):
    return [
        (target_node, val_node, flags[target_node.id])
        for (
            _assign,
            target_node,
            val_node,
            _val,
        ) in ipynb._iter_source_val_assigns(source)
        if target_node.id in flags
    ]


def _tokenize_source(source):
    return list(tokenize.generate_tokens(io.StringIO(six.text_type(source)).readline))


class _ReplaceAssignsState(object):
    def __init__(self, assigns):
        self.assigns = assigns
        self.repl_tokens = []
        self.line_offset = 0
        self.col_offset = 0


def _tok_type(t):
    return t[0]


def _tok_str(t):
    return t[1]


def _tok_start(t):
    return t[2]


def _tok_end(t):
    return t[3]


def _replace_assigns_for_tokens(tokens, assigns):
    state = _ReplaceAssignsState(assigns)
    while tokens:
        t = tokens.pop(0)
        _maybe_reset_col_offset(t, state)
        _handle_token_for_replace_assigns(t, tokens, state)
    return state.repl_tokens


def _maybe_reset_col_offset(t, state):
    if state.repl_tokens:
        t_line = _tok_start(t)[0]
        state_repl_line = _tok_end(state.repl_tokens[-1])[0]
        if t_line + state.line_offset != state_repl_line:
            state.col_offset = 0


def _handle_token_for_replace_assigns(t, tokens, state):
    if _tok_type(t) == token.NAME:
        _handle_name_token_for_replace_assigns(t, tokens, state)
    else:
        _add_token_for_replace_assigns(t, state)


def _add_token_for_replace_assigns(t, state):
    repos_t = _reposition_token(t, state.line_offset, state.col_offset)
    state.repl_tokens.append(repos_t)


def _reposition_token(t, line_offset, start_offset):
    t_start = _tok_start(t)
    t_end = _tok_end(t)
    end_offset = start_offset if t_start[0] == t_end[0] else 0
    return (
        t[0],
        t[1],
        (t_start[0] + line_offset, t_start[1] + start_offset),
        (t_end[0] + line_offset, t_end[1] + end_offset),
        t[4],
    )


def _handle_name_token_for_replace_assigns(t, tokens, state):
    _add_token_for_replace_assigns(t, state)
    assign = _maybe_assign_for_token(t, state)
    if assign:
        _handle_assign_for_replace_assigns(assign, tokens, state)


def _maybe_assign_for_token(t, state):
    assign_key = (_tok_str(t), _tok_start(t))
    try:
        return state.assigns[assign_key]
    except KeyError:
        return None


def _handle_assign_for_replace_assigns(assign, tokens, state):
    try:
        t = tokens.pop(0)
    except IndexError:
        pass
    else:
        _add_token_for_replace_assigns(t, state)
        if _tok_is_assign_op(t):
            _handle_assign_op_for_replace_assigns(assign, tokens, state)


def _tok_is_assign_op(t):
    return _tok_type(t) == token.OP and _tok_str(t) == "="


def _handle_assign_op_for_replace_assigns(assign, tokens, state):
    _handle_pre_value_tokens_for_replace_assigns(tokens, assign, state)
    _handle_value_tokens_for_replace_assigns(tokens, assign, state)


def _handle_pre_value_tokens_for_replace_assigns(tokens, assign, state):
    while tokens:
        t = tokens[0]
        if _is_assign_value_token(t, assign):
            break
        del tokens[0]
        _add_token_for_replace_assigns(t, state)


def _is_assign_value_token(t, assign):
    _target, val_node, _flag_val = assign
    return (
        _tok_start(t) == (val_node.lineno, val_node.col_offset)
        or val_node.col_offset == -1
        and _tok_end(t)[0] == val_node.lineno
    )


def _handle_value_tokens_for_replace_assigns(tokens, assign, state):
    _target, _val_node, flag_val = assign
    cur_val_tokens = _pop_value_tokens(tokens)
    assert cur_val_tokens
    _handle_replacement_value_for_replace_assigns(flag_val, cur_val_tokens, state)


def _pop_value_tokens(tokens):
    val_tokens = []
    while tokens:
        val_tokens.append(tokens.pop(0))
        if _is_python_expr(val_tokens):
            break
    return val_tokens


def _is_python_expr(tokens):
    s = tokenize.untokenize(tokens).strip()
    try:
        m = ast.parse(s)
    except SyntaxError:
        return False
    else:
        assert len(m.body) == 1 and isinstance(m.body[0], ast.Expr), m.body
        return True


def _handle_replacement_value_for_replace_assigns(val, replaced_tokens, state):
    val_tokens = _val_tokens(val)
    repl_tokens, repl_line_offset, repl_col_offset = _replace_tokens(
        replaced_tokens, val_tokens
    )
    for t in repl_tokens:
        _add_token_for_replace_assigns(t, state)
    state.line_offset += repl_line_offset

    state.col_offset += repl_col_offset


def _val_tokens(val):
    val_repr = six.text_type(repr(val))
    gen_tokens = tokenize.generate_tokens(io.StringIO(val_repr).readline)
    return _maybe_strip_newline(_strip_endmarker(gen_tokens))


def _strip_endmarker(tokens):
    tokens = list(tokens)
    assert _tok_type(tokens[-1]) == token.ENDMARKER, tokens
    return tokens[:-1]


def _maybe_strip_newline(tokens):
    assert tokens
    if _tok_type(tokens[-1]) == token.NEWLINE:
        return tokens[:-1]
    return tokens


def _replace_tokens(cur_tokens, new_tokens):
    assert cur_tokens
    assert new_tokens
    cur_start = _tok_start(cur_tokens[0])
    line = cur_start[0]
    pos = cur_start[1]
    repl_tokens = []
    for t in new_tokens:
        line_end = line + _token_line_offset(t)
        pos_end = pos + _token_pos_offset(t)
        repl_tokens.append(
            (
                t[0],
                t[1],
                (line, pos),
                (line_end, pos_end),
                t[4],
            )
        )
        line = line_end
        pos = pos_end
    cur_end = _tok_end(cur_tokens[-1])
    repl_end = _tok_end(repl_tokens[-1])
    line_offset = repl_end[0] - cur_end[0]
    pos_offset = repl_end[1] - cur_end[1]
    return repl_tokens, line_offset, pos_offset


def _token_line_offset(t):
    return t[3][0] - t[2][0]


def _token_pos_offset(t):
    if _token_line_offset(t) < 0:
        return 0
    return t[3][1] - t[2][1]


def _print_output(notebook):
    for stream, out in _iter_notebook_output(notebook):
        stream.write(out)


def _iter_notebook_output(notebook):
    nb_data = json.load(open(notebook))
    for cell in nb_data.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        cell_execution_count = cell.get("execution_count", "?")
        for output in cell.get("outputs", []):
            output_type = output.get("output_type")
            if output_type == "stream":
                stream = sys.stderr if output.get("name") == "stderr" else sys.stdout
                for part in output.get("text", []):
                    yield stream, part
            elif output_type == "execute_result":
                yield sys.stdout, "Out[%s]: " % cell_execution_count
                data = output.get("data", {})
                for part in data.get("text/plain", []):
                    yield sys.stdout, part
                yield sys.stdout, "\n"


def _save_images(notebook):
    if os.getenv("NB_NO_IMAGES") == "1":
        return
    logged = False
    for filename, img_bytes in _iter_notebook_images(notebook):
        if not logged:
            log.info("Saving images")
            logged = True
        with open(filename, "wb") as f:
            f.write(img_bytes)


def _iter_notebook_images(notebook):
    nb_data = json.load(open(notebook))
    notebook_base = os.path.splitext(notebook)[0]
    for cell in nb_data.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        cell_execution_count = cell.get("execution_count", "?")
        output_pos = 0
        for output in cell["outputs"]:
            if output.get("output_type") != "display_data":
                continue
            data = output.get("data", {})
            encoded = data.get("image/png")
            if not encoded:
                continue
            try:
                img_bytes = base64.b64decode(encoded)
            except Exception as e:
                log.warning(
                    "error decoding image at pos %i in In[%s]: %s",
                    output_pos,
                    cell_execution_count,
                    e,
                )
            else:
                filename = "%s_%s_%i.png" % (
                    notebook_base,
                    cell_execution_count,
                    output_pos,
                )
                yield filename, img_bytes


def _nbconvert_html(notebook):
    notebook_relpath = _relpath(notebook)
    cmd = [
        "jupyter-nbconvert",
        "-y",
        "--log-level",
        "WARN",
        "--to",
        "html",
        notebook_relpath,
    ]
    log.debug("jupyter-nbconvert cmd: %s", cmd)
    log.info("Saving HTML")
    returncode = subprocess.call(cmd)
    if returncode != 0:
        sys.exit(returncode)


if __name__ == "__main__":
    main()
