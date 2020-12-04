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
    flags = _init_flags(run, rest_args)
    run_notebook = _init_run_notebook(args.notebook, flags, run)
    if args.no_exec or os.getenv("NB_NO_EXEC") == "1":
        log.info("Skipping execute (NB_NO_EXEC specified)")
        return
    _nbexec(run_notebook)
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
        "configuration issues"
    )
    sys.exit(1)


def _apply_flags_to_notebook(state):
    nb_data = json.load(open(state.notebook_path))
    for cell in nb_data.get("cells", []):
        _apply_flags_to_cell_source(cell, state)
    json.dump(nb_data, open(state.notebook_path, "w"))


def _apply_flags_to_cell_source(cell, state):
    try:
        source_lines = cell["source"]
    except KeyError:
        pass
    else:
        repl_source_lines = _apply_flags_to_source_lines(source_lines, state)
        cell["source"] = repl_source_lines


def _apply_flags_to_source_lines(source_lines, state):
    source = "".join(source_lines).rstrip()
    source = _replace_flag_pattern_vals(source, state)
    source = _replace_flag_assign_vals(source, state)
    return [line + "\n" for line in source.split("\n")]


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
        for _assign, target_node, val_node, _val in ipynb._iter_source_val_assigns(
            source
        )
        if target_node.id in flags
    ]


def _tokenize_source(source):
    return list(tokenize.generate_tokens(io.StringIO(six.text_type(source)).readline))


def _replace_assigns_for_tokens(tokens, assigns):
    assign = None
    have_op = False
    repl_tokens = []
    cur_line = 0
    col_offset = 0
    line_offset = 0

    for t0 in tokens:
        if t0[2][0] + line_offset != cur_line:
            col_offset = 0
        t = _apply_t_offsets(t0, line_offset, col_offset)
        cur_line = t[2][0]
        if have_op:
            assert assign is not None
            _target, val_node, flag_val = assign
            if t0[2] == (val_node.lineno, val_node.col_offset) or (
                val_node.col_offset == -1 and t0[3][0] == val_node.lineno
            ):
                val_t = _val_token(flag_val)
                repl_t, repl_line_offset, repl_col_offset = _replace_token(t, val_t)
                line_offset += repl_line_offset
                col_offset = repl_col_offset
                repl_tokens.append(repl_t)
                have_op = False
                assign = None
            else:
                repl_tokens.append(t)
        elif assign:
            assert not have_op
            if t[0] == token.OP and t[1] == "=":
                have_op = True
            else:
                assign = None
            repl_tokens.append(t)
        elif t[0] == token.NAME:
            try:
                assign = assigns[(t0[1], t0[2])]
            except KeyError:
                pass
            repl_tokens.append(t)
        else:
            repl_tokens.append(t)

    return repl_tokens


def _apply_t_offsets(t, line_offset, start_offset):
    end_offset = start_offset if t[2][0] == t[3][0] else 0
    return (
        t[0],
        t[1],
        (t[2][0] + line_offset, t[2][1] + start_offset),
        (t[3][0] + line_offset, t[3][1] + end_offset),
        t[4],
    )


def _val_token(val):
    val_repr = six.text_type(repr(val))
    gen_tokens = tokenize.generate_tokens(io.StringIO(val_repr).readline)
    return list(gen_tokens)[0]


def _replace_token(cur_t, new_t):
    cur_line_offset = _token_line_offset(cur_t)
    assert _token_line_offset(new_t) == 0, new_t  # cur vals must be on one line
    new_pos_offset = _token_pos_offset(new_t)
    repl_pos_offset = new_pos_offset - _token_pos_offset(cur_t)
    repl_t = (
        new_t[0],
        new_t[1],
        (cur_t[2][0], cur_t[2][1]),
        (cur_t[2][0], cur_t[2][1] + new_pos_offset),
        new_t[4],
    )
    return repl_t, -cur_line_offset, repl_pos_offset


def _token_line_offset(t):
    return t[3][0] - t[2][0]


def _token_pos_offset(t):
    if _token_line_offset(t) < 0:
        return 0
    return t[3][1] - t[2][1]


def _nbexec(notebook):
    cmd = [
        "jupyter-nbconvert",
        "--to",
        "notebook",
        "--execute",
        "--inplace",
        notebook,
    ]
    returncode = subprocess.call(cmd)
    if returncode != 0:
        sys.exit(returncode)


def _nbconvert_html(notebook):
    cmd = [
        "jupyter-nbconvert",
        "--to",
        "html",
        notebook,
    ]
    returncode = subprocess.call(cmd)
    if returncode != 0:
        sys.exit(returncode)


if __name__ == "__main__":
    main()
