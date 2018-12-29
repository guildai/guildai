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

import click

from guild import click_util

from . import remote_support

@click.command()
@click.option(
    "-T", "--tests", "all_tests",
    help="Run Guild test suite.",
    is_flag=True)
@click.option(
    "-t", "--test", "tests", metavar="TEST",
    help="Run `TEST` (may be used multiple times).",
    multiple=True)
@click.option(
    "-n", "--no-info",
    help="Don't print info (useful when just running tests).",
    is_flag=True)
@click.option(
    "-s", "--skip", metavar="TEST",
    help="Skip `TEST` when running Guild test suite. Ignored otherwise.",
    multiple=True)
@click.option("-v", "--verbose", help="Show more information.", is_flag=True)
@remote_support.remote_option("Check remote environment.")
@click.option("--uat", hidden=True, is_flag=True)

@click_util.use_args

def check(args):
    """Check the Guild setup.

    This command performs a number of checks and prints information
    about the Guild setup.

    You can also run the Guild test suite by specifying the `--tests`
    option.

    """
    from . import check_impl
    check_impl.main(args)
