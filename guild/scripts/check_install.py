# This is free and unencumbered software released into the public
# domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a
# compiled binary, for any purpose, commercial or non-commercial, and
# by any means.
#
# In jurisdictions that recognize copyright laws, the author or
# authors of this software dedicate any and all copyright interest in
# the software to the public domain. We make this dedication for the
# benefit of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to
# this software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org>

from __future__ import absolute_import
from __future__ import print_function

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
