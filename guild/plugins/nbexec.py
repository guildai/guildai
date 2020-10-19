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
    executed_notebook = _nbexec(args.notebook, flags, run)
    _nbconvert_html(executed_notebook)


def _init_logging():
    op_util.init_logging()
    globals()["log"] = logging.getLogger("guild")


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("notebook")
    return p.parse_known_args()


def _check_env():
    nbconvert = util.which("jupyter-nbconvert")
    if not nbconvert:
        log.error(
            "jupyter-nbconvert is required to run Notebooks - "
            "install it by running 'pip install jupyter' and try again"
        )
        sys.exit(1)


def _nbexec(notebook, flags, run):
    working_notebook = _init_notebook(notebook, flags, run)
    cmd = [
        "jupyter-nbconvert",
        "--to",
        "notebook",
        "--execute",
        "--inplace",
        working_notebook,
    ]
    returncode = subprocess.call(cmd)
    if returncode != 0:
        sys.exit(returncode)
    return working_notebook


def _init_notebook(notebook, flags, run):
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
        "Use 'guild run OP --test-sourcecode to debug source code configuration issues"
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
            _replace_flag_refs(line, non_null_flags, flags_extra) for line in source
        ]


def _replace_flag_refs(s, flags, flags_extra):
    for flag_name, extra in flags_extra.items():
        try:
            repl_config = extra["nb-repl"]
            flag_val = flags[flag_name]
        except KeyError:
            pass
        else:
            assert flag_val is not None, flag_name
            if isinstance(repl_config, six.string_types):
                repl_config = [repl_config]
            for repl in repl_config:
                s_mod = _replace_flag_ref(repl, flag_val, s)
                _debug_log_repl(s, s_mod, repl, flag_name, flag_val)
                s = s_mod
    return s


def _replace_flag_ref(pattern, val, s):
    try:
        m = re.search(pattern, s, re.MULTILINE)
    except ValueError:
        return s
    else:
        if not m:
            return s
        formatted_val = repr(val)
        parts = []
        cur = 0
        for slice_start, slice_end in m.regs[1:]:
            parts.append(s[cur:slice_start])
            parts.append(formatted_val)
            cur = slice_end
        parts.append(s[cur:])
        return "".join(parts)


def _debug_log_repl(s0, s1, repl, flag_name, flag_val):
    if log.getEffectiveLevel() > logging.DEBUG:
        return
    if s0 != s1:
        log.debug("nb-repl: %r -> %r (%s=%r via %r", s0, s1, flag_name, flag_val, repl)
    else:
        log.debug("nb-repl: %r unchanged (%s=%r via %r", s0, flag_name, flag_val, repl)


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
