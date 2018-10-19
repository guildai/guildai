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

import click

from guild import click_util

@click.command()
@click.argument("path-or-package", required=False)
@click.option(
    "-t", "--test", "tests",
    metavar="[TEST]...",
    required=False,
    multiple=True,
    help="Run a specific test. May be used multiple times.")
@click.option(
    "-m", "--model",
    metavar="MODEL",
    multiple=True,
    help=(
        "Only test operations for MODEL. May be used multiple times. "
        "Use with `--operation` to further limit tests."))
@click.option(
    "-o", "--operation",
    metavar="NAME",
    multiple=True,
    help=(
        "Only test operation NAME. May be used multiple times. "
        "Use with `--model` to limit operation to specific models."))
@click.option(
    "-1", "--one-model", is_flag=True,
    help=(
        "Only test operations for the first model in a for-each-model "
        "step."))
@click.option(
    "-s", "--stop-on-fail", is_flag=True,
    help="Stop testing after the first failed test.")
@click.option(
    "--gpus", metavar="DEVICES",
    help=("Limit availabe GPUs to DEVICES, a comma separated list of "
          "device IDs. By default all GPUs are available. Cannot be"
          "used with --no-gpus."))
@click.option(
    "--no-gpus", is_flag=True,
    help="Disable GPUs for tests. Cannot be used with --gpu.")

@click.option(
    "-y", "--yes", is_flag=True,
    help="Do not prompt before running tests.")

@click.pass_context
@click_util.use_args

def test(ctx, args):
    """Run model or package tests.

    By default, tests are run for a Guild file in the current
    directory. `PATH_OR_PACKGE` may be specified to run tests in a
    different directory or for an installed package.

    Use one or more `--test` options to run specific tests in the
    order specified. If no tests are specified, runs all of the tests
    defined in the referenced Guild file or package.

    Use one or more `--model` or `--operation` options to limit tests
    to the specified models and operations respectively.

    In cases where multiple models may be tested in a
    ``for-each-model`` step, you may use `--one-model` to limit tests
    to the first model. This is useful for reducing the test time at
    the expense of test coverage.

    By default all tests are run even if one or more tests fail. To
    stop testing on the first failed test, use `--stop-on-fail`.

    ### Environments

    Tests are run in the current environment. If you want to isolate
    tests from other environments, you must create a test-specific
    environment activate it before running ``test``.

    """
    from . import test_impl
    test_impl.main(args, ctx)
