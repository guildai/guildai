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
import json
import logging
import os
import re
import shutil
import subprocess
import sys

import six

from guild import op_util
from guild import util

log = None  # initialized in _init_logging


def main():
    _init_logging()
    args, rest_args = _parse_args()
    run = op_util.current_run()
    _check_env()
    flags, other_args = op_util.args_to_flags(rest_args)
    if other_args:
        log.warning(
            "unexpected args: %s",
            " ".join([util.shlex_quote(arg) for arg in other_args]),
        )
    working_notebook = _init_working_notebook(args.notebook, flags, run)
    if os.getenv("NBINIT_ONLY") == "1":
        log.info("NBINIT_ONLY set, skipping Notebook execute")
        return
    _nbexec(working_notebook, flags, run)
    _nbconvert_html(working_notebook)


def _init_logging():
    op_util.init_logging()
    globals()["log"] = logging.getLogger("guild")


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("notebook")
    return p.parse_known_args()


def _check_env():
    _check_nbconvert()
    _check_nbextensions()


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


def _init_working_notebook(notebook, flags, run):
    src = _find_notebook(notebook)
    dest = os.path.join(run.dir, os.path.basename(src))
    shutil.copyfile(src, dest)
    _apply_flags_to_notebook(dest, flags, run)
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


def _apply_flags_to_notebook(notebook, flags, run):
    flags_extra = run.get("op", {}).get("flags-extra")
    nb_data = json.load(open(notebook))
    for cell in nb_data.get("cells", []):
        _apply_flags_to_cell_source(cell, flags, flags_extra)
    json.dump(nb_data, open(notebook, "w"))


def _apply_flags_to_cell_source(cell, flags, flags_extra):
    non_null_flags = {name: val for name, val in flags.items() if val is not None}
    try:
        source = cell["source"]
    except KeyError:
        pass
    else:
        cell["source"] = [
            _update_source_line(line, non_null_flags, flags_extra) for line in source
        ]


def _update_source_line(line, flags, flags_extra):
    line = _replace_flag_refs(line, flags, flags_extra)
    return line

def _replace_flag_refs(s, flags, flags_extra):
    for flag_name, flag_val, config in _iter_flag_replace_config(flags, flags_extra):
        for replace_pattern in config:
            s_mod = _replace_flag_ref(replace_pattern, flag_val, s)
            _debug_log_repl(s, s_mod, replace_pattern, flag_name, flag_val)
            s = s_mod
    return s


def _iter_flag_replace_config(flags, flags_extra):
    for flag_name, extra in flags_extra.items():
        try:
            repl_config = extra["nb-replace"]
            flag_val = flags[flag_name]
        except KeyError:
            pass
        else:
            assert flag_val is not None, flag_name
            yield flag_name, flag_val, _coerce_repl_config_to_list(repl_config)


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
        # No replacement groups so assume entire match is replaced
        return m.regs
    else:
        # Only use explicit replacement groups
        return m.regs[1:]


def _debug_log_repl(s0, s1, repl, flag_name, flag_val):
    if log.getEffectiveLevel() > logging.DEBUG:
        return
    if s0 != s1:
        log.debug(
            "nb-replace: %r -> %r (%s=%r via %r)",
            s0,
            s1,
            flag_name,
            flag_val,
            repl,
        )
    else:
        log.debug(
            "nb-replace: %r unchanged (%s=%r via %r)",
            s0,
            flag_name,
            flag_val,
            repl,
        )


def _nbexec(notebook, flags, run):
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
