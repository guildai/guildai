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
import re
import shlex

from guild import cli
from guild import modelfile
from guild import plugin

def _train_opdef(name, modeldef, parent_opdef, local_train_op):
    local_train = _local_train_opdef(local_train_op, modeldef, name)
    data = _train_opdef_data(local_train)
    return _gen_opdef(name, data, modeldef, local_train, parent_opdef)

def _local_train_opdef(op_name, modeldef, requiring_op):
    op_name = op_name or "train"
    opdef = modeldef.get_operation(op_name)
    if not opdef:
        cli.error(
            "operation '%s' not defined in %s (required by %s)"
            % (op_name, modeldef.modelfile.src, requiring_op))
    return opdef

def _train_opdef_data(local_train):
    module_name, cmd_args = _split_cmd(local_train.cmd)
    cmd = _op_cmd("train", cmd_args)
    return {
        "description": "Train a model in Cloud ML",
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
            },
            "config": {
                "description": "Path to the Cloud ML job configuration file"
            }
        },
        "remote": True
    }

def _op_cmd(name, args):
    args = " ".join([pipes.quote(arg) for arg in args])
    return "guild.plugins.cloudml_op_main {} {}".format(name, args)

def _split_cmd(s):
    parts = shlex.split(s)
    return parts[0], parts[1:]

def _gen_opdef(name, data, modeldef, local_opdef, parent_opdef):
    opdef = modelfile.OpDef(name, data, modeldef)
    opdef.update_flags(local_opdef)
    opdef.update_dependencies(local_opdef)
    if parent_opdef:
        opdef.update_flags(parent_opdef)
        opdef.update_dependencies(parent_opdef)
    return opdef

def _hptune_opdef(name, modeldef, parent_opdef, local_train_op):
    local_train = _local_train_opdef(local_train_op, modeldef, name)
    data = _train_opdef_data(local_train)
    data["cmd"] = data["cmd"].replace(
        "guild.plugins.cloudml_op_main train",
        "guild.plugins.cloudml_op_main hptune")
    data["description"] = (
        "Optimize model hyperparameters in Cloud ML\n"
        "\n"
        "A config file defining a hyperparameter spec is required for "
        "this operation. See https://goo.gl/aZQYCe for spec details.\n"
        "\n"
        "You may override values in the config using flags. See support "
        "config flags below for more information."
    )
    data["flags"]["config"]["required"] = True
    data["flags"].update({
        "max-trials": {
            "description": (
                "Maximum number of trials for hyperparameter tuning\n"
                "\n"
                "Overrides maxTrials in config."
            )
        },
        "max-parallel-trials": {
            "description": (
                "Maximum number of parallel trials for hyperparameter tuning\n"
                "\n"
                "Overrides maxParallelTrials in config."
            )
        },
        "resume-from": {
            "description": (
                "Resume hyperparameter tuning using the results of "
                "previous cloudml-hptune operation\n"
                "\n"
                "Use the ID of the run you want to resume from."
            )
        }
    })
    return _gen_opdef(name, data, modeldef, local_train, parent_opdef)

class CloudMLPlugin(plugin.Plugin):

    op_patterns = [
        (re.compile(r"cloudml-train(?:#(.*))?"), _train_opdef),
        (re.compile(r"cloudml-hptune(?:#(.*))?"), _hptune_opdef)
    ]

    def get_operation(self, name, model, parent_opdef):
        for p, handler in self.op_patterns:
            m = p.match(name)
            if m:
                return handler(name, model.modeldef, parent_opdef, *m.groups())

    def sync_run(self, run, watch=False, **_kw):
        from . import cloudml_op_main
        cloudml_op_main.sync_run(run, watch)

    def stop_run(self, run, no_wait=False, **_kw):
        from . import cloudml_op_main
        cloudml_op_main.stop_run(run, no_wait)
