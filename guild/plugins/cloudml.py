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

import pipes
import shlex

from guild import cli
from guild import modelfile
from guild import plugin

def _train_opdef(name, modeldef, config):
    local_train = _local_train_op(modeldef, config, name)
    module_name, cmd_args = _split_cmd(local_train.cmd)
    cmd = _op_cmd("train", cmd_args)
    data = {
        "cmd": cmd,
        "flags": {
            "bucket-name": {
                "description": (
                    "Name of bucket to use for run data storage"
                ),
                "required": True
            },
            "module-name": {
                "description": "Training module",
                "default": module_name
            },
            "scale-tier": {
                "description": (
                    "Cloud ML resources allocated to a training job\n"
                    "\n"
                    "Use STANDARD_1 for many workers and a few parameter "
                    "servers.\n"
                    "\n"
                    "Use PREMIUM_1 for a large number of workers with many "
                    "parameter servers.\n"
                    "\n"
                    "Use BASIC_GPU for a single worker instance with a GPU."
                ),
                "default": "BASIC"
            }
        }
    }
    opdef = modelfile.OpDef(name, data, modeldef)
    opdef.update_flags(local_train)
    opdef.update_dependencies(local_train)
    if config:
        opdef.update_flags(config)
        opdef.update_dependencies(config)
    return opdef

def _op_cmd(name, args):
    args = " ".join([pipes.quote(arg) for arg in args])
    return "guild.plugins.cloudml_op_main {} {}".format(name, args)

def _local_train_op(modeldef, config, cloudml_op):
    op_name = (config and config.get_flag_value("train-op")) or "train"
    op = modeldef.get_operation(op_name)
    if not op:
        cli.error(
            "operation '%s' not defined in %s (required by %s)"
            % (op_name, modeldef.modelfile.src, cloudml_op))
    return op

def _split_cmd(s):
    parts = shlex.split(s)
    return parts[0], parts[1:]

class CloudMLPlugin(plugin.Plugin):

    def get_operation(self, name, model, config):
        if name == "cloudml-train":
            return _train_opdef(name, model.modeldef, config)
        elif name == "cloudml-deploy":
            raise AssertionError("TODO")
        return None

    def sync_run(self, run, watch=False, **_kw):
        from . import cloudml_op_main
        cloudml_op_main.sync_run(run, watch)
