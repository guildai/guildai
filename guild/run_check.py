# Copyright 2017-2019 TensorHub, Inc.
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

import difflib
import glob
import logging
import os
import re

from guild import util

log = logging.getLogger("guild")

class Failed(Exception):
    pass

class FileCheck(object):

    type_attr = "file"

    def __init__(self, data):
        self.path = data[self.type_attr]
        self.compare_to = data.get("compare-to")
        self.pattern = data.get("contains")
        self.pattern_re = _compile_pattern(self.pattern)

    def check_run(self, run):
        log.info("checking run %s files %r", run.id, self.path)
        path_glob = os.path.join(run.path, self.path)
        matches = glob.glob(path_glob)
        if not matches:
            raise Failed(
                "no files matching %s in run %s"
                % (self.path, run.id))
        for path in matches:
            self._check_path(path, run)

    def _check_path(self, path, run):
        rel_path = os.path.relpath(path, run.path)
        if self.compare_to:
            compare_to = os.path.join(
                run.path, _apply_env_to_path(self.compare_to))
            log.info(
                "comparing run %s file %s to %s",
                run.id, rel_path, compare_to)
            _compare_files(path, compare_to)
        if self.pattern_re:
            log.info(
                "checking run %s file %s for %r",
                run.id, rel_path, self.pattern)
            out = _read(path)
            if not self.pattern_re.search(out):
                raise Failed(
                    "could not find pattern %r in run %s file %s"
                    % (self.pattern, run.id, rel_path))

class OutputCheck(object):

    type_attr = "output"

    def __init__(self, data):
        self.pattern = data[self.type_attr]
        self.pattern_re = _compile_pattern(self.pattern)

    def check_run(self, run):
        log.info("checking run %s output for %r", run.id, self.pattern)
        output_path = run.guild_path("output")
        out = _read(output_path)
        if not self.pattern_re.search(out):
            raise Failed(
                "could not find pattern %r in run %s output"
                % (self.pattern, run.id))

def _compile_pattern(pattern):
    if pattern is None:
        return None
    try:
        return re.compile(pattern)
    except Exception:
        raise ValueError("invalid regular expression: %r" % pattern)

def _compare_files(actual, expected):
    _compare(_read(actual), _read(expected), actual, expected)

def _compare(actual, expected, actual_src, expected_src):
    a = re.split(r"\n\r?", expected)
    b = re.split(r"\n\r?", actual)
    fromfile = expected_src
    tofile = actual_src
    diff = list(difflib.unified_diff(a, b, fromfile, tofile))
    if diff:
        log.error("\n".join(diff))
        raise Failed("unexpected file contents - see above for details")

def _read(path):
    try:
        return open(path, "r").read()
    except Exception:
        raise Failed("error reading run output from %s" % path)

def _apply_env_to_path(path):
    """Replaces occurrences of ${NAME} with env values."""
    return util.resolve_refs(path, os.environ)

check_classes = [FileCheck, OutputCheck]

def init_check(data):
    for cls in check_classes:
        if cls.type_attr in data:
            return cls(data)
    raise ValueError(
        "invalid check config - expected one of: %s"
        % ", ".join([cls.type_attr for cls in check_classes]))
