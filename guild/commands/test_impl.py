# Copyright 2017-2018 TensorHub, Inc.
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

from guild import cli
from guild import cmd_impl_support
from guild import test as testlib

def main(args):
    gf = cmd_impl_support.path_or_package_guildfile(args.path_or_package)
    tests = [_gf_test(name, gf) for name in _test_names(gf, args)]
    if not tests:
        _no_tests_error(gf)
    gpus = _test_gpus(args)
    if args.yes or _confirm_tests(tests):
        _run_tests(tests, gpus, args)

def _test_names(gf, args):
    return args.tests or [t.name for t in gf.tests]

def _gf_test(name, gf):
    try:
        return gf.get_test(name)
    except ValueError:
        cli.error("test '%s' not defined in %s" % (name, gf.src))

def _no_tests_error(gf):
    cli.out("There are no tests defined in %s" % gf.src, err=True)
    cli.error(exit_status=2)

def _test_gpus(args):
    if args.no_gpus and args.gpus:
        cli.error("--gpus and --no-gpus cannot both be used")
    if args.no_gpus:
        return ""
    elif args.gpus:
        return args.gpus
    else:
        return None # use all available (default)

def _confirm_tests(tests):
    cli.out("You are about to run the following tests:")
    test_data = [
        dict(name=t.name, desc=_line1(t.description))
        for t in tests
    ]
    cli.table(test_data, ["name", "desc"], indent=2)
    return cli.confirm("Continue?", default=True)

def _line1(s):
    return s.split("\n")[0]

def _run_tests(tests, gpus, args):
    failed = False
    config = testlib.TestConfig(
        models=args.model,
        operations=args.operation,
        gpus=gpus)
    for test in tests:
        try:
            testlib.run_guildfile_test(test, config)
        except testlib.TestError as e:
            _test_failed_msg(test, e)
            failed = True
            if args.stop_on_fail:
                break
    if failed:
        _some_tests_failed_msg()
        cli.error()
    cli.out(cli.style("All tests passed", bold=True))

def _test_failed_msg(test, e):
    msg = "Test %s failed: %s" % (test.name, e)
    cli.out(cli.style(msg, bold=True, fg="red"), err=True)

def _some_tests_failed_msg():
    msg = "One or more tests failed - see above for details"
    cli.out(cli.style(msg, bold=True, fg="red"), err=True)
