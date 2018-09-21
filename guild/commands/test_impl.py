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

def main(args):
    gf = cmd_impl_support.dir_or_package_guildfile(args.path_or_package)
    tests = [_gf_test(name, gf) for name in _test_names(gf, args)]
    if not tests:
        cli.info("Nothing to test", err=True)
        cli.error(2)
    for test in tests:
        print("TODO: test ze models yo", test)

def _test_names(gf, args):
    return args.tests or [t.name for t in gf.tests]

def _gf_test(name, gf):
    try:
        return gf.get_test(name)
    except ValueError:
        cli.error("test '%s' not defined in %s" % (name, gf.src))
