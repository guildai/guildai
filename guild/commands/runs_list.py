# Copyright 2017 TensorHub, Inc.
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
from . import runs_support

def runs_list_options(fn):
    click_util.append_params(fn, [
        click.Option(
            ("-v", "--verbose"),
            help="Show run details.",
            is_flag=True),
        click.Option(
            ("-d", "--deleted"),
            help="Show deleted runs.",
            is_flag=True),
    ])
    runs_support.op_and_label_filters(fn)
    runs_support.status_filters(fn)
    runs_support.scope_options(fn)
    return fn

@click.command("list, ls")
@runs_list_options

@click_util.use_args
@click_util.render_doc

def list_runs(args):
    """List runs.

    Run lists may be filtered using a variety of options. See below
    for details.

    Run indexes are included in list output for a specific listing,
    which is based on the available runs, their states, and the
    specified filters. You may use the indexes in run selection
    commands (e.g. ``runs delete``, ``compare``, etc.) but note that
    these indexes will change as runs are started, deleted, or run
    status changes.

    To show run detail, use `--verbose`.

    {{ runs_support.op_and_label_filters }}
    {{ runs_support.status_filters }}
    {{ runs_support.scope_options }}

    ### Show deleted runs

    Use `--deleted` to show deleted runs. You can use the listing for
    run IDs and indexes to use in ``runs restore`` (restore runs) and
    ``runs purge`` (permanently delete runs).

    """
    from . import runs_impl
    runs_impl.list_runs(args)
