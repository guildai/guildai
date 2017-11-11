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

import guild.run

from guild import cmd_impl_support
from guild import var

def main(args):
    run = cmd_impl_support.one_run([
        guild.run.Run(id, path) for id, path in var.find_runs(args.run)
    ], args.run)
    if args.clear:
        run.del_attr("label")
    else:
        run.write_attr("label", args.label)
