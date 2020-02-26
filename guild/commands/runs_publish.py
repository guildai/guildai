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

from . import runs_support


def publish_params(fn):
    click_util.append_params(
        fn,
        [
            runs_support.runs_arg,
            click.Option(
                ("-d", "--dest"), metavar="DIR", help="Destination to publish runs."
            ),
            click.Option(
                ("-t", "--template"),
                metavar="VAL",
                help="Run template used to publish runs.",
            ),
            click.Option(
                ("-i", "--index-template"),
                metavar="VAL",
                help="Index template used to publish runs.",
            ),
            click.Option(
                ("-f", "--files"), help="Publish default run files.", is_flag=True
            ),
            click.Option(
                ("-a", "--all-files"), help="Publish all run files.", is_flag=True
            ),
            click.Option(
                ("-L", "--include-links"),
                help="Include links when publishing files. Implies --files.",
                is_flag=True,
            ),
            click.Option(
                ("--no-md5",),
                help="Do not calculate MD5 digests for run files.",
                is_flag=True,
            ),
            click.Option(
                ("--include-batch",), help="Include batch runs.", is_flag=True
            ),
            click.Option(
                ("-r", "--refresh-index"),
                help="Refresh runs index without publishing anything.",
                is_flag=True,
            ),
            runs_support.all_filters,
            click.Option(
                ("-y", "--yes"), help="Do not prompt before publishing.", is_flag=True
            ),
        ],
    )
    return fn


@click.command("publish")
@publish_params
@click.pass_context
@click_util.use_args
@click_util.render_doc
def publish_runs(ctx, args):
    """Publish one or more runs.

    By default, runs are published to 'published-runs'
    subdirectory. To specify a different location, use `--dest`.

    A published run is a subdirectory of destination `DIR` that
    contains run-specific files:

    - `run.yml` - run information (e.g. run ID, operation, status,
      etc.)

    - `flags.yml` - run flags

    - `output.txt` - run output written to stdout/stderr

    - `scalars.csv` - summary of run scalar values

    - `files.csv` - list of files associated with the run

    - `code/` - subdirectory containing project source code at the
      time run was started

    - `runfiles/` - files associated with the run

    {{ runs_support.runs_arg }}

    {{ runs_support.all_filters }}

    """
    from . import runs_impl

    runs_impl.publish(args, ctx)
