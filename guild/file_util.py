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

import fnmatch
import glob
import hashlib
import logging
import os
import re
import shutil

import six

from guild import util

log = logging.getLogger("guild")


class FileSelect(object):
    def __init__(self, root, rules):
        self.root = root
        self.rules = rules
        self._disabled = None

    @property
    def disabled(self):
        if self._disabled is None:
            self._disabled = self._init_disabled()
        return self._disabled

    def _init_disabled(self):
        """Returns True if file select is disabled.

        Assumes not disabled until finds a disable all pattern (untyped
        match of '*'). Disable pattern can be reset by any include
        pattern.
        """
        disabled = False
        for rule in self.rules:
            if rule.result:
                disabled = False
            elif "*" in rule.patterns and rule.type is None:
                disabled = True
        return disabled

    def select_file(self, src_root, relpath):
        """Apply rules to file located under src_root with relpath.

        All rules are applied to the file. The last rule to apply
        (i.e. its `test` method returns a non-None value) determines
        whether or not the file is selected - selected if test returns
        True, not selected if returns False.

        If no rules return a non-None value, the file is not selected.

        Returns a tuple of the selected flag (True or False) and list
        of applied rules and their results (two-tuples).
        """
        rule_results = [
            (rule.test(src_root, relpath), rule)
            for rule in self.rules
            if rule.type != "dir"
        ]
        result, _test = reduce_file_select_results(rule_results)
        return result is True, rule_results

    def prune_dirs(self, src_root, relroot, dirs):
        pruned = []
        for name in sorted(dirs):
            last_rule_result = None
            relpath = os.path.join(relroot, name)
            for rule in self.rules:
                if rule.type != "dir":
                    continue
                rule_result, _test = rule.test(src_root, relpath)
                if rule_result is not None:
                    last_rule_result = rule_result
            if last_rule_result is False:
                log.debug("skipping directory %s", relpath)
                pruned.append(name)
                dirs.remove(name)
        return pruned


def reduce_file_select_results(results):
    """Reduces a list of file select results to a single determining result."""
    for (result, test), _rule in reversed(results):
        if result is not None:
            return result, test
    return None, None


class FileSelectRule(object):
    def __init__(
        self,
        result,
        patterns,
        type=None,
        regex=False,
        sentinel=None,
        size_gt=None,
        size_lt=None,
        max_matches=None,
    ):
        self.result = result
        if isinstance(patterns, six.string_types):
            patterns = [patterns]
        if not regex:
            patterns = _native_paths(patterns)
        self.patterns = patterns
        self.regex = regex
        self._patterns_match = self._patterns_match_f(patterns, regex)
        self.type = self._validate_type(type)
        self.sentinel = sentinel
        self.size_gt = size_gt
        self.size_lt = size_lt
        self.max_matches = max_matches
        self._matches = 0

    def _patterns_match_f(self, patterns, regex):
        if regex:
            return self._regex_match_f(patterns)
        else:
            return self._fnmatch_f(patterns)

    @staticmethod
    def _regex_match_f(patterns):
        compiled = [re.compile(p) for p in patterns]
        return lambda path: any((p.match(util.norm_path_sep(path)) for p in compiled))

    @staticmethod
    def _fnmatch_f(patterns):
        return lambda path: any((_fnmatch(path, p) for p in patterns))

    @staticmethod
    def _validate_type(type):
        valid = ("text", "binary", "dir")
        if type is not None and type not in valid:
            raise ValueError(
                "invalid value for type %r: expected one of %s"
                % (type, ", ".join(valid))
            )
        return type

    @property
    def matches(self):
        return self._matches

    def reset_matches(self):
        self._matches = 0

    def test(self, src_root, relpath):
        fullpath = os.path.join(src_root, relpath)
        tests = [
            FileSelectTest("max matches", self._test_max_matches),
            FileSelectTest("pattern", self._test_patterns, relpath),
            FileSelectTest("type", self._test_type, fullpath),
            FileSelectTest("size", self._test_size, fullpath),
        ]
        for test in tests:
            if not test():
                return None, test
        self._matches += 1
        return self.result, None

    def _test_max_matches(self):
        if self.max_matches is None:
            return True
        return self._matches < self.max_matches

    def _test_patterns(self, path):
        return self._patterns_match(path)

    def _test_type(self, path):
        if self.type is None:
            return True
        if self.type == "text":
            return self._test_text_file(path)
        elif self.type == "binary":
            return self._test_binary_file(path)
        elif self.type == "dir":
            return self._test_dir(path)
        else:
            assert False, self.type

    @staticmethod
    def _test_text_file(path):
        return util.safe_is_text_file(path)

    @staticmethod
    def _test_binary_file(path):
        return not util.safe_is_text_file(path)

    def _test_dir(self, path):
        if not os.path.isdir(path):
            return False
        if self.sentinel:
            return glob.glob(os.path.join(path, self.sentinel))
        return True

    def _test_size(self, path):
        if self.size_gt is None and self.size_lt is None:
            return True
        size = util.safe_filesize(path)
        if size is None:
            return True
        if self.size_gt and size > self.size_gt:
            return True
        if self.size_lt and size < self.size_lt:
            return True
        return False


def _native_paths(patterns):
    return [p.replace("/", os.path.sep) for p in patterns]


def _fnmatch(path, pattern):
    if os.path.sep not in pattern:
        path = os.path.basename(path)
    pattern = _strip_leading_path_sep(pattern)
    return fnmatch.fnmatch(path, pattern)


def _strip_leading_path_sep(pattern):
    while pattern:
        if pattern[0] != os.path.sep:
            break
        pattern = pattern[1:]
    return pattern


class FileSelectTest(object):
    def __init__(self, name, test_f, *test_args):
        self.name = name
        self.test_f = test_f
        self.test_args = test_args

    def __call__(self):
        return self.test_f(*self.test_args)


def include(patterns, **kw):
    return FileSelectRule(True, patterns, **kw)


def exclude(patterns, **kw):
    return FileSelectRule(False, patterns, **kw)


class FileCopyHandler(object):
    def __init__(self, src_root, dest_root, select):
        self.src_root = src_root
        self.dest_root = dest_root
        self.select = select

    def copy(self, path, _rule_results):
        src = os.path.join(self.src_root, path)
        dest = os.path.join(self.dest_root, path)
        log.debug("copying %s to %s", src, dest)
        util.ensure_dir(os.path.dirname(dest))
        self._try_copy_file(src, dest)

    def _try_copy_file(self, src, dest):
        try:
            shutil.copyfile(src, dest)
            shutil.copymode(src, dest)
        except IOError as e:
            if e.errno != 2:  # Ignore file not exists
                if not self.handle_copy_error(e, src, dest):
                    raise
        except OSError as e:  # pylint: disable=duplicate-except
            if not self.handle_copy_error(e, src, dest):
                raise

    def ignore(self, _path, _rule_results):
        pass

    @staticmethod
    def handle_copy_error(_e, _src, _dest):
        return False


def copytree(dest, select, root_start=None, followlinks=True, handler_cls=None):
    """Copies files to dest for a FileSelect.

    root_start is an optional location from which select.root, if
    relative, starts. Defaults to os.curdir.

    If followlinks is True (the default), follows linked directories
    when copying the tree.

    A handler class may be specified to create a handler of copy
    events. FileCopyHandler is used by default. If specified, the
    class is used to instantiate a handler with `(src, dest,
    select)`. Handler methods `copy()` and `ignore()` are called with
    `(relpath, results)` where `results` is a list of results from
    each rule as `(result, rule)` tuples.

    As an optimization, `copytree` skips evaluation of files if the
    file select is disabled. File selects are disabled if no files can
    be selected for their rules. If select is disabled and a handler
    class is specified, the handler is still instantiated, however, no
    calls to `copy()` or `ignore()` will be made.
    """
    src = _copytree_src(root_start, select)
    # Instantiate handler as part of the copytree contract.
    handler = (handler_cls or FileCopyHandler)(src, dest, select)
    if select.disabled:
        return
    for root, dirs, files in os.walk(src, followlinks=followlinks):
        dirs.sort()
        relroot = _relpath(root, src)
        pruned = select.prune_dirs(src, relroot, dirs)
        for name in pruned:
            relpath = os.path.join(relroot, name)
            handler.ignore(relpath, [])
        for name in sorted(files):
            relpath = os.path.join(relroot, name)
            selected, results = select.select_file(src, relpath)
            if selected:
                handler.copy(relpath, results)
            else:
                handler.ignore(relpath, results)


def _copytree_src(root_start, select):
    root_start = root_start or os.curdir
    if select.root:
        return os.path.join(root_start, select.root)
    return root_start


def _relpath(path, start):
    if path == start:
        return ""
    return os.path.relpath(path, start)


def files_digest(root):
    files = _files_for_digest(root)
    if not files:
        return None
    md5 = hashlib.md5()
    for path in files:
        normpath = _normalize_path_for_digest(path, root)
        md5.update(_encode_file_path_for_digest(normpath))
        md5.update(b"\x00")
        _apply_digest_file_bytes(path, md5)
        md5.update(b"\x00")
    return md5.hexdigest()


def _files_for_digest(root):
    all = []
    for path, _dirs, files in os.walk(root, followlinks=False):
        for name in files:
            all.append(os.path.join(path, name))
    all.sort()
    return all


def _normalize_path_for_digest(path, root):
    relpath = os.path.relpath(path, root)
    return relpath.replace(os.path.sep, "/")


def _encode_file_path_for_digest(path):
    return path.encode("UTF-8")


def _apply_digest_file_bytes(path, d):
    BUF_SIZE = 1024 * 1024
    with open(path, "rb") as f:
        while True:
            buf = f.read(BUF_SIZE)
            if not buf:
                break
            d.update(buf)


def disk_usage(path):
    total = _file_size(path)
    for root, dirs, names in os.walk(path, followlinks=False):
        for name in dirs + names:
            path = os.path.join(root, name)
            total += _file_size(os.path.join(root, name))
    return total


def _file_size(path):
    stat = os.lstat if os.path.islink(path) else os.stat
    try:
        return stat(path).st_size
    except (OSError, IOError) as e:
        log.warning("could not read size of %s: %s", path, e)
        return 0


def find(root, followlinks=False, includedirs=False):
    all = []
    relpath = lambda path, name: (os.path.relpath(os.path.join(path, name), root))
    for path, dirs, files in os.walk(root, followlinks=followlinks):
        for name in dirs:
            if includedirs or os.path.islink(os.path.join(path, name)):
                all.append(relpath(path, name))
        for name in files:
            all.append(relpath(path, name))
    return sorted(all)
