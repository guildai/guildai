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

import platform
import re
import sys

from pip._internal.commands import install

def main(args):
    req, finder = _parse_args(args)
    _print_req(req)
    _print_system_info()
    _print_valid_tags(finder)
    _print_candidates(finder, req)

def _parse_args(args):
    cmd = install.InstallCommand()
    options, cmd_args = cmd.parse_args(args)
    if len(cmd_args) != 1:
        _usage_error()
    return cmd_args[0], _init_finder(options, cmd)

def _usage_error():
    sys.stderr.write(
        "usage: %s [options] <requirement specifier>\n"
        % sys.argv[0])
    sys.exit(1)

def _init_finder(options, cmd):
    session = cmd._build_session(options)
    if options.python_version:
        python_versions = [options.python_version]
    else:
        python_versions = None
    return cmd._build_package_finder(
        options=options,
        session=session,
        platform=options.platform,
        python_versions=python_versions,
        abi=options.abi,
        implementation=options.implementation)

def _print_req(req):
    print("Requirement specifier: %s" % req)

def _print_system_info():
    print("System info:")
    print("  python executable: %s" % sys.executable)
    print("  python version: %s" % re.sub(r"\s+", " ", sys.version))
    print("  platform: %s" % " ".join(platform.uname()))
    print("  architecture: %s" % " ".join(platform.architecture()))

def _print_valid_tags(finder):
    print("Valid tags:")
    for tags in finder.candidate_evaluator._valid_tags:
        print("  %s" % " ".join(tags))

class SkippedLinks(object):

    def __init__(self, finder):
        self._finder = finder
        self._skipped = []
        self._log_skipped_link0 = None

    def __enter__(self):
        self._log_skipped_link0 = self._finder._log_skipped_link
        self._finder._log_skipped_link = self._log_skipped_link
        return self._skipped

    def _log_skipped_link(self, link, reason):
        self._skipped.append((link, reason))

    def __exit__(self, *_exc):
        self._finder._log_skipped_link = self._log_skipped_link0

def _print_candidates(finder, req):
    with SkippedLinks(finder) as skipped:
        candidates = finder.find_candidates(req)
    _print_skipped_candidates(skipped)
    _print_all_candidates(candidates)
    _print_applicable_candidates(candidates)
    _print_best_candidate(candidates)

def _print_skipped_candidates(skipped):
    print("Skipped candidates:")
    for link, reason in skipped:
        print("  %s: %s" % (link, reason))

def _print_all_candidates(candidates):
    print("All candidates:")
    for c in candidates.iter_all():
        print("  %s" % c.location)

def _print_applicable_candidates(candidates):
    print("Applicable candidates:")
    for c in candidates.iter_all():
        print("  %s" % c.location)

def _print_best_candidate(candidates):
    best = candidates.get_best()
    print("Best candidate:")
    if best:
        print("  %s" % best.location)
    else:
        print(" <none>")

if __name__ == "__main__":
    main(sys.argv[1:])
