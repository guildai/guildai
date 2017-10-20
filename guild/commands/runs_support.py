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

RUN_ARG_HELP = """
RUN may be a run ID (or the unique start of a run ID) or a zero-based
index corresponding to a run returned by the list command. Indexes may
also be specified in ranges in the form START:END where START is the
start index and END is the end index. Either START or END may be
omitted. If START is omitted, all runs up to END are selected. If END
id omitted, all runs from START on are selected. If both START and END
are omitted (i.e. the ':' char is used by itself) all runs are selected.
"""

def run_scope_options(fn):
    click_util.append_params(fn, [
        click.Option(
            ("-a", "--all"),
            help="Include all runs.",
            is_flag=True)
    ])
    return fn

def run_filters(fn):
    click_util.append_params(fn, [
        click.Option(
            ("-m", "--model", "models"), metavar="MODEL",
            help="Include only runs for MODEL.",
            multiple=True),
        click.Option(
            ("-r", "--running", "status"),
            help="Include only runs that are still running.",
            flag_value="running"),
        click.Option(
            ("-c", "--completed", "status"),
            help="Include only completed runs.",
            flag_value="completed"),
        click.Option(
            ("-s", "--stopped", "status"),
            help=("Include only runs that exited with an error or were "
                  "terminated by the user."),
            flag_value="stopped"),
        click.Option(
            ("-e", "--error", "status"),
            help="Include only runs that exited with an error.",
            flag_value="error"),
        click.Option(
            ("-t", "--terminated", "status"),
            help="Include only runs terminated by the user.",
            flag_value="terminated"),
    ])
    return fn

def runs_list_options(fn):
    run_scope_options(fn)
    run_filters(fn)
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
    return fn
