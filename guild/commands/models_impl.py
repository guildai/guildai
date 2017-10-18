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

import guild.cli
import guild.cmd_impl_support

def main(args, ctx):
    project = guild.cmd_impl_support.project_for_location(
        args.project_location, ctx)
    guild.cli.table(
        [_format_model(model) for model in project],
        cols=["name", "description"],
        detail=(["source", "version", "operations"]
                if args.verbose else []))

def _format_model(model):
    return {
        "source": model.project.src,
        "name": model.name,
        "version": model.version,
        "description": model.description or "",
        "operations": ", ".join([op.name for op in model.operations])
    }
