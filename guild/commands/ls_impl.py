# Copyright 2017-2022 RStudio, PBC
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

import fnmatch
import logging
import os

from guild import cli
from guild import run_manifest
from guild import util

from . import remote_impl_support
from . import runs_impl

log = logging.getLogger("guild")


def main(args, ctx):
    if args.remote:
        _check_ignored_remote_opts(args)
        remote_impl_support.list_files(args)
    else:
        _main(args, ctx)


def _check_ignored_remote_opts(args):
    if args.full_path:
        log.warning("--full-path is not supported for remote file lists - ignoring")


def _main(args, ctx):
    if args.path and os.path.isabs(args.path):
        cli.error("PATH must be relative\nTry 'guild ls --help' for more information.")
    run = runs_impl.one_run(args, ctx)
    _print_header(run, args)
    _print_file_listing(run, args)


def _print_header(run, args):
    if not args.full_path and not args.no_format:
        cli.out(f"{_header(run, args)}:")


def _header(run, args):
    dir = run.dir
    if os.getenv("NO_HEADER_PATH") == "1":
        dir = os.path.basename(dir)
    return dir if args.full_path else util.format_dir(dir)


def _print_file_listing(run, args):
    for val in list_run_files(run, args):
        _print_path(val, args)


def list_run_files(run, args):
    return util.natsorted(_iter_files(run, args))


def _iter_files(run, args):
    path_filter = _path_filter(run, args)
    for root, dirs, files in os.walk(run.dir, followlinks=args.follow_links):
        for name in dirs + files:
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, run.dir)
            if path_filter.match(rel_path):
                yield _format_list_path(full_path, rel_path, args)
            else:
                if name in dirs:
                    path_filter.maybe_delete_dir(name, rel_path, dirs)


def _path_filter(run, args):
    base_path_filter = _base_path_filter(args)
    manifest_file_types = _manifest_file_types(args)
    if manifest_file_types:
        return _ManifestFilter(run, manifest_file_types, base_path_filter)
    return base_path_filter


def _base_path_filter(args):
    all = _all_flag_for_args(args)
    if args.path:
        if _is_pattern(args.path):
            return _PatternFilter(args.path, all)
        return _PathFilter(args.path, all)
    return _DefaultFilter(all)


def _all_flag_for_args(args):
    # If any of the file type flags are specified (i.e. sourcecode,
    # dependencies, or generated) show all files to ensure they are listed even
    # if they're in hidden directories.
    return args.all or args.sourcecode or args.dependencies or args.generated


def _manifest_file_types(args):
    return [
        x[1]
        for x in (
            (args.sourcecode, "s"),
            (args.dependencies, "d"),
            (args.generated, "g"),
        )
        if x[0]
    ]


class _DefaultFilter:
    """Filters out hidden files unless configured to show all files."""

    def __init__(self, all):
        self.all = all

    def match(self, path):
        if self.all:
            return True
        return not _is_hidden_name(_split_path(path)[-1])

    def maybe_delete_dir(self, name, _path, dirs):
        if self.all:
            return
        if _is_hidden_name(name):
            dirs.remove(name)


def _is_hidden_name(path):
    return path[:1] == "."


def _is_pattern(s):
    return "*" in s or "?" in s


class _PatternFilter:
    def __init__(self, pattern, all):
        self.pattern_parts = _split_path(pattern)
        self.all = all

    def match(self, path):
        path_parts = _split_path(path)
        return _match_path_parts(path_parts, self.pattern_parts, self.all)

    def maybe_delete_dir(self, name, path, dirs):
        path_parts = _split_path(path)
        if self.all or not _is_hidden_name(name):
            return
        if len(self.pattern_parts) >= len(path_parts):
            if not _is_hidden_name(self.pattern_parts[len(path_parts) - 1]):
                dirs.remove(name)


def _match_path_parts(path_parts, pattern_parts, all):
    if len(path_parts) < len(pattern_parts):
        return False
    for i, pattern_part in enumerate(pattern_parts):
        if not fnmatch.fnmatch(path_parts[i], pattern_part):
            return False
    if not all:
        for i, path_part in enumerate(path_parts):
            if _is_hidden_name(path_part):
                maybe_pattern = pattern_parts[i] if i < len(pattern_parts) else None
                if not maybe_pattern or not _is_hidden_name(maybe_pattern):
                    return False
    return True


class _PathFilter:
    def __init__(self, path, all):
        self.match_parts = _split_path(path)
        self.all = all

    def match(self, path):
        path_parts = _split_path(path)
        if not self.all and _is_hidden_name(path_parts[-1]):
            return path_parts == self.match_parts
        return _is_subpath(self.match_parts, path_parts)

    def maybe_delete_dir(self, name, path, dirs):
        path_parts = _split_path(path)
        if not _is_subpath(path_parts, self.match_parts):
            dirs.remove(name)


def _is_subpath(maybe_subpath, path):
    if len(path) < len(maybe_subpath):
        return False
    for i, subpath_part in enumerate(maybe_subpath):
        if subpath_part != path[i]:
            return False
    return True


def _split_path(path):
    return [part for part in path.split(os.path.sep) if part]


class _ManifestFilter:
    """Filters based on manifest type.

      's' -> file is source code
      'd' -> file is a dependency
      'g' -> file is generated

    Note that 'g' is a virtual manigest type -- this type does not exist in a
    manifest by definition but is inferred by the absence of a manifest entry.
    """

    def __init__(self, run, entry_types, base_filter):
        self.run = run
        self.entry_types = tuple(entry_types)
        self.index = _init_manifest_index(run)
        self.base_filter = base_filter

    def match(self, path):
        if not os.path.isfile(os.path.join(self.run.dir, path)):
            return False
        entry_type = self.index.get(path)
        if not entry_type:
            if _split_path(path)[0] == ".guild":
                return False
            entry_type = "g"
        return entry_type in self.entry_types and self.base_filter.match(path)

    def maybe_delete_dir(self, name, path, dirs):
        self.base_filter.maybe_delete_dir(name, path, dirs)


def _init_manifest_index(run):
    with run_manifest.manifest_for_run(run.dir) as m:
        return {entry[1]: entry[0] for entry in m}


def _format_list_path(full_path, rel_path, args):
    path = full_path if args.full_path else rel_path
    return _ensure_trailing_slash_for_dir(path, full_path)


def _ensure_trailing_slash_for_dir(path, full_path):
    if os.path.isdir(full_path) and full_path[:-1] != os.path.sep:
        return path + os.path.sep
    return path


def _print_path(path, args):
    if args.full_path:
        path = os.path.abspath(path)
    if not path:
        return
    if args.no_format or args.full_path:
        cli.out(path)
    else:
        cli.out(f"  {path}")
