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

import tempfile

from guild import cli
from guild import cmd_impl_support
from guild import test as testlib
from guild import util

def main(args):
    gf = cmd_impl_support.dir_or_package_guildfile(args.path_or_package)
    tests = [_gf_test(name, gf) for name in _test_names(gf, args)]
    if not tests:
        _no_tests_error(gf)
    if args.yes or _confirm_tests(tests, args):
        _run_tests(tests, args)

def _confirm_tests(tests, args):
    if args.no_env:
        env_desc = " (no environment)"
    elif args.env:
        env_desc = " (environment %s)" % args.env
    else:
        env_desc = " (new environment"
        if args.clean_env:
            env_desc += ", auto-delete"
        env_desc += ")"
    prompt = ["You are about to run the following tests%s:" % env_desc]
    prompt.extend(["  " + t.name for t in tests])
    prompt.append("Continue?")
    return cli.confirm("\n".join(prompt), default=True)

def _run_tests(tests, args):
    env_dir, rm_env_dir = _init_env_dir(args)
    if env_dir:
        cli.out("Running tests in environment %s" % env_dir)
    for test in tests:
        testlib.run_guildfile_test(test, env_dir)
    if rm_env_dir:
        cli.out("Deleting environment %s" % env_dir)
        util.safe_rmtree(env_dir)
    elif env_dir:
        cli.out("Keeping environment %s" % env_dir)

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

def _init_env_dir(args):
    if args.no_env and args.env:
        cli.error("--no-env and --env cannot both be used")
    if args.clean_env and args.env:
        cli.error("--clean-env and --env cannot both be used")
    if args.no_env:
        return None, False
    if args.env:
        return args.env, False
    return tempfile.mkdtemp(prefix="guild-env-"), args.clean_env
