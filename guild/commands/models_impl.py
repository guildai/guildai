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

from guild import cli
from guild.cmd_impl_support import init_model_path
from guild.model import iter_models

def main(args, ctx):
    init_model_path(ctx, args.all)
    cli.table(
        [_format_model(model, long_names=args.all) for model in iter_models()],
        cols=["fullname", "description"],
        detail=(["name", "source", "operations"] if args.verbose else [])
    )

def _format_model(model, long_names):
    modeldef = model.modeldef
    if long_names:
        fullname = "%s/%s"  % (model.dist.project_name, modeldef.name)
    else:
        fullname = modeldef.name
    return {
        "fullname": fullname,
        "source": modeldef.modelfile.src,
        "name": modeldef.name,
        "description": modeldef.description or "",
        "operations": ", ".join([op.name for op in modeldef.operations])
    }
