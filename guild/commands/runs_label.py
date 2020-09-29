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
from . import runs_support


def label_params(fn):
    click_util.append_params(
        fn,
        [
            runs_support.runs_arg,
            click.Option(("-s", "--set"), metavar="VAL", help="Set VAL as label."),
            click.Option(
                ("-p", "--prepend"),
                metavar="VAL",
                help="Prepend VAL to existing label.",
            ),
            click.Option(
                ("-a", "--append"), metavar="VAL", help="Append VAL to existing label."
            ),
            click.Option(
                ("-rm", "--remove"),
                metavar="VAL",
                multiple=True,
                help="Remove VAL from existing label. May be used multiple times.",
            ),
            click.Option(
                ("-c", "--clear"), help="Clear the entire run label.", is_flag=True
            ),
            runs_support.all_filters,
            remote_support.remote_option("Label remote runs."),
            click.Option(
                ("-y", "--yes"),
                help="Do not prompt before modifying labels.",
                is_flag=True,
            ),
        ],
    )
    return fn


@click.command("label")
@label_params
@click.pass_context
@click_util.use_args
@click_util.render_doc
def label_runs(ctx, args):
    """Set run labels.

    The label action may be specified using one of three mutually
    exclusive options: `--label`, `--prepend`, or
    `--append`. `--label` sets the entire run label. `--prepend`
    appends the specified value to the existing label, and `--append`
    appends the value.

    Use `--remove` to remove the specified value from a label, if it
    exists. Use `--clear` to remove the entire label.

    `--tag` and `--untag` are aliases for `--prepend` and `--remove`
    respectively.

    Specify runs to modify using one or more `RUN` arguments. See
    SPECIFYING RUNS for more information.

    If `RUN` is not specified, the most recent run is selected.

    By default Guild will prompt you before making any changes. If you
    want to apply the changes without being prompted, use the
    ``--yes`` option.

    {{ runs_support.runs_arg }}

    If a `RUN` argument is not specified, ``1`` is assumed (the most
    recent run).

    {{ runs_support.all_filters }}

    ### Label Remote Runs

    To label remote runs, use `--remote`.

    {{ remote_support.remote_option }}

    """
    from . import runs_impl

    runs_impl.label(args, ctx)
