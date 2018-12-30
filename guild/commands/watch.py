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

from . import remote_support # pylint: disable=unused-import
from . import runs_support

@click.command()

@runs_support.run_arg
@runs_support.op_and_label_filters
@remote_support.remote_option("Watch a remote run.")
@click.option(
    "--pid", metavar="PID",
    help=("Watch the run associated with the specified process. "
          "PID may be a process ID or a path to a file containing "
          "a process ID."))

@click.pass_context
@click_util.use_args
@click_util.render_doc

def watch(ctx, args):
    """Watch run output.

    By default, the command will watch output from the current running
    operation.

    {{ runs_support.run_arg }}
    {{ runs_support.op_and_label_filters }}

    ### Watching remote runs

    Use `--remote` to watch a remote run.

    {{ remote_support.remote_option }}

    ### Watching run by PID

    You may alternatively specify the process ID of the run to watch,
    using `--pid`. ``PID`` may be a process ID or a path to a file
    containing a process ID.

    PID may not be specified with other options.

    """
    from . import watch_impl
    watch_impl.main(args, ctx)
