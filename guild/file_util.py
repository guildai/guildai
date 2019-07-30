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

import fnmatch
import os
import shutil

import six

from guild import util

class FileSelect(object):

    def __init__(self, root, rules):
        self.root = root
        self.rules = rules

    def select_file(self, src_root, relpath):
        last_rule_result = None
        for rule in self.rules:
            rule_result = rule.test(src_root, relpath)
            if rule_result is not None:
                last_rule_result = rule_result
        return last_rule_result is True

class FileSelectRule(object):

    def __init__(self, result, patterns):
        self.result = result
        if isinstance(patterns, six.string_types):
            patterns = [patterns]
        self.patterns = patterns

    def test(self, src_root, relpath):
        return util.find_apply([
            lambda: self._test_patterns(relpath),
            lambda: None,
        ])

    def _test_patterns(self, path):
        if any((fnmatch.fnmatch(path, p) for p in self.patterns)):
            return self.result
        return None

def include(patterns):
    return FileSelectRule(True, patterns)

def exclude(patterns):
    return FileSelectRule(False, patterns)

class DebugCallback(object):
    pass

class FileCopyHandler(object):

    def __init__(self, src_root, dest_root, debug_cb=None, error_handler=None):
        self.src_root = src_root
        self.dest_root = dest_root
        self.debug_cb = debug_cb
        self.error_handler = error_handler

    def copy(self, path):
        src = os.path.join(self.src_root, path)
        dest = os.path.join(self.dest_root, path)
        util.ensure_dir(os.path.dirname(dest))
        self._try_copy_file(src, dest)

    def _try_copy_file(self, src, dest):
        try:
            shutil.copyfile(src, dest)
        except IOError as e:
            if e.errno != 2: # Ignore file not exists
                if not self.error_handler:
                    raise
                self.error_handler(e)
        except OSError as e:
            if not self.error_handler:
                raise
            self.error_handler(e)

    def ignore(self, path):
        pass

def copytree(dest, select, root_start=None, followlinks=True, debug_cb=None):
    """Copies files to dest for a FileSelect.

    root_start is an optional location from which select.root, if
    relative, starts. Defaults to os.curdir.

    If followlinks is True (the default), follows linked directories
    when copying the tree.

    If debug_cb is specified, does not copy files but instead invokes
    debub_cb methods as it evaluates source files to copy. debug_cb
    must implement the DebugCallback interface.
    """
    src = _copytree_src(root_start, select)
    handler = FileCopyHandler(src, dest, debug_cb)
    for root, dirs, files in os.walk(src, followlinks=followlinks):
        ##select.prune_dirs(src, root, dirs)
        relroot = _relpath(root, src)
        for name in files:
            relpath = os.path.join(relroot, name)
            if select.select_file(src, relpath):
                handler.copy(relpath)
            else:
                handler.ignore(relpath)

def _copytree_src(root_start, select):
    root_start = root_start or os.curdir
    if select.root:
        return os.path.join(root_start, select.root)
    return root_start

def _relpath(path, start):
    if path == start:
        return ""
    return os.path.relpath(path, start)
