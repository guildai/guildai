# Copyright 2017-2023 Posit Software, PBC
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

import json

import click

from guild import click_util


def output_options(fn):
    click_util.append_params(
        fn,
        [
            click.Option(
                ("-f", "--format"),
                is_flag=True,
                help="Format the JSON outout.",
            )
        ],
    )
    return fn


def out(data, args):
    print(_encode_data(data, args))


def _encode_data(data, args):
    json_opts = {"indent": 2, "sort_keys": True} if args.format else {}
    return json.dumps(data, **json_opts)
