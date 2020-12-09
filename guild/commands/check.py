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

import click

from guild import click_util

from . import remote_support


def _ac_all_tests(incomplete, ctx, **_kw):
    if ctx.params.get("remote"):
        return []
    return _ac_builtin_tests(incomplete, ctx) + click_util.completion_filename(
        ext=["md", "txt"]
    )


def _ac_builtin_tests(incomplete, ctx, **_kw):
    from guild import _test

    if ctx.params.get("remote"):
        return []
    return [t for t in _test.all_tests() if t.startswith(incomplete)]


@click.command()
@click.option("--env", help="Limit check to environment info.", is_flag=True)
@click.option("-tf", "--tensorflow", help="Check TensorFlow status.", is_flag=True)
@click.option("-pt", "--pytorch", help="Check PyTorch status.", is_flag=True)
@click.option("-T", "--tests", "all_tests", help="Run Guild test suite.", is_flag=True)
@click.option(
    "-t",
    "--test",
    "tests",
    metavar="TEST",
    help="Run `TEST` (may be used multiple times).",
    multiple=True,
    autocompletion=_ac_all_tests,
)
@click.option(
    "-n",
    "--no-info",
    help="Don't print info (useful when just running tests).",
    is_flag=True,
)
@click.option(
    "-s",
    "--skip",
    metavar="TEST",
    help="Skip `TEST` when running Guild test suite. Ignored otherwise.",
    multiple=True,
    autocompletion=_ac_builtin_tests,
)
@click.option("-v", "--verbose", help="Show more information.", is_flag=True)
@click.option("--space", help="Show disk space usage for Guild files.", is_flag=True)
@click.option("--version", metavar="REQUIRED", help="Check the installed version.")
@click.option(
    "--notify", is_flag=True, help="Send system notification when check is complete."
)
@remote_support.remote_option("Check remote environment.")
@click.option(
    "--offline/--no-offline",
    default=None,
    help="Don't check guild.ai for latest versions.",
    is_flag=True,
)
@click.option("--check-url", hidden=True, default="http://api.guild.ai/check")
@click.option("--uat", hidden=True, is_flag=True)
@click_util.use_args
def check(args):
    """Check the Guild setup.

    This command performs a number of checks and prints information
    about the Guild installation.

    Run the Guild test suite by specifying the `--tests` option.

    Run a test file using `--test FILE`. Test files must be valid
    doctest files. See https://docs.python.org/library/doctest.html
    for details.

    To verify that the installed version of Guild matches a required
    spec, use `--version`. REQUIRED can be any valid version
    requirement. For example, to confirm that Guild is at least
    version 0.7.0, use `--version '>=0.7.0'`. Note you must quote
    arguments that contain less-than or greater-than symbols in POSIX
    shells.
    """
    from . import check_impl

    check_impl.main(args)
