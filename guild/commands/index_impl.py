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

import json

import guild.index

from guild import cli
from guild import util

def main(args):
    index = guild.index.RunIndex()
    if args.operation == "sync":
        _sync(index)
    elif args.operation == "raw-fields":
        _print_fields(index)
    else:
        _print_info(index)

def _sync(index):
    cli.out("Updating index")
    index.sync()

def _print_fields(index):
    fields = list(index.ix.reader().all_stored_fields())
    json_out = json.dumps(
        fields,
        sort_keys=True,
        indent=4,
        separators=(',', ': '))
    cli.out(json_out)

def _print_info(index):
    cli.out("path: {}".format(index.path))
    cli.out("runs: {}".format(index.ix.doc_count()))
    last_modified = util.format_timestamp(index.ix.last_modified() * 1000000)
    cli.out("last-modified: {}".format(last_modified))
