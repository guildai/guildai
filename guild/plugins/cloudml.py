# Copyright 2017-2018 TensorHub, Inc.
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
from guild import guildfile
from guild import plugin

from . import cloudml_op_main

def _gen_opdef(name, data, modeldef, parent_opdef=None, local_opdef=None):
    opdef = guildfile.OpDef(name, data, modeldef)
    if local_opdef:
        opdef.update_flags(local_opdef)
        opdef.update_dependencies(local_opdef)
    if parent_opdef:
        opdef.update_flags(parent_opdef)
        opdef.update_dependencies(parent_opdef)
    return opdef

def _train_opdef(name, modeldef, parent_opdef, local_train_op):
    local_train = _local_train_opdef(local_train_op, modeldef, name)
    data = _train_opdef_data(local_train)
    return _gen_opdef(name, data, modeldef, parent_opdef, local_train)

def _local_train_opdef(op_name, modeldef, requiring_op):
    op_name = op_name or "train"
    opdef = modeldef.get_operation(op_name)
    if not opdef:
        cli.error(
            "operation '%s' not defined in %s (required by %s)"
            % (op_name, modeldef.guildfile.src, requiring_op))
    return opdef

def _train_opdef_data(local_train):
    module_name, cmd_args = _split_cmd(local_train.cmd)
    main = _op_main("train", cmd_args)
    return {
        "description": "Train a model in Cloud ML",
        "main": main,
        "flags": {
            "bucket": {
                "description": (
                    "Google Cloud Storage bucket used to store run data"
                ),
                "required": True
            },
            "region": {
                "description": (
                    "Region traning job is submitted to"
                ),
                "default": cloudml_op_main.DEFAULT_REGION
            },
            "job-name": {
                "description": (
                    "Job name to submit (default is generated using the "
                    "training run ID)"
                )
            },
            "runtime-version": {
                "description": (
                    "TensorFlow runtime version"
                ),
                "default": cloudml_op_main.DEFAULT_RUNTIME_VERSION
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
                "description": "Path to a Cloud ML job configuration file"
            },
        },
        "remote": True
    }

def _op_main(name, args=None):
    args = " ".join([pipes.quote(arg) for arg in (args or [])])
    return "guild.plugins.cloudml_op_main {} {}".format(name, args)

def _split_cmd(s):
    parts = shlex.split(s)
    return parts[0], parts[1:]

def _hptune_opdef(name, modeldef, parent_opdef, local_train_op):
    local_train = _local_train_opdef(local_train_op, modeldef, name)
    data = _train_opdef_data(local_train)
    data["main"] = data["main"].replace(
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
    return _gen_opdef(name, data, modeldef, parent_opdef, local_train)

def _deploy_opdef(name, modeldef, parent_opdef):
    data = _deploy_opdef_data()
    return _gen_opdef(name, data, modeldef, parent_opdef)

def _deploy_opdef_data():
    return {
        "description": "Deploy a model to Cloud ML",
        "main": _op_main("deploy"),
        "flags": {
            "trained-model": {
                "description": (
                    "Run ID associated with the trained model (default is "
                    "latest cloudml-train run)"
                )
            },
            "version": {
                "description": (
                    "Name of the deployed Cloud ML version (default is "
                    "generated using the current timestamp)"
                )
            },
            "bucket": {
                "description": (
                    "Google Cloud Storage bucket used to store model binaries "
                    "(required if 'model-binaries' is not specified)"
                )
            },
            "model-binaries": {
                "description": (
                    "Google Cloud Storage path to store model binaries "
                    "(required if 'bucket' is not specified)"
                )
            },
            "model": {
                "description": (
                    "Name of the deployed Cloud ML model (default is "
                    "generated using the run model)"
                )
            },
            "runtime-version": {
                "description": (
                    "TensorFlow runtime version"
                ),
                "default": cloudml_op_main.DEFAULT_RUNTIME_VERSION
            },
            "config": {
                "description": "Path to a Cloud ML job configuration file"
            }
        }
    }

def _predict_opdef(name, modeldef, parent_opdef):
    data = _predict_opdef_data()
    return _gen_opdef(name, data, modeldef, parent_opdef)

def _predict_opdef_data():
    return {
        "description": "Send a prediction request to Cloud ML",
        "main": _op_main("predict"),
        "flags": {
            "deployed-model": {
                "description": (
                    "Run ID associated with the deployed model (default is "
                    "latest cloudml-resource run)"
                )
            },
            "instances": {
                "description": (
                    "File containing the instances to make predictions on"
                ),
                "required": True
            },
            "instance-type": {
                "description": (
                    "Instance type (if type cannot be inferred from instances "
                    "file name)"
                ),
                "choices": ["json", "text"]
            },
            "output-format": {
                "description": (
                    "Format of the prediction output "
                    "(see https://cloud.google.com/sdk/gcloud/reference/ for "
                    "supported values)"
                )
            }
        }
    }

def _batch_predict_opdef(name, modeldef, parent_opdef):
    data = _batch_predict_opdef_data()
    return _gen_opdef(name, data, modeldef, parent_opdef)

def _batch_predict_opdef_data():
    data = _predict_opdef_data()
    data.update({
        "description": "Submit a prediction job to Cloud ML",
        "main": _op_main("batch-predict")
    })
    data["flags"].update({
        "bucket": {
            "description": (
                "Google Cloud Storage bucket used to store run data"
            ),
            "required": True
        },
        "region": {
            "description": (
                "Region prediction job is submitted to"
            ),
            "default": cloudml_op_main.DEFAULT_REGION
        },
        "job-name": {
            "description": (
                "Job name to submit (default is generated using the "
                "predction run ID)"
            )
        }
    })
    return data

class CloudMLPlugin(plugin.Plugin):

    op_patterns = [
        (re.compile(r"cloudml-train(?:#(.*))?"), _train_opdef),
        (re.compile(r"cloudml-hptune(?:#(.*))?"), _hptune_opdef),
        (re.compile(r"cloudml-deploy"), _deploy_opdef),
        (re.compile(r"cloudml-predict"), _predict_opdef),
        (re.compile(r"cloudml-batch-predict"), _batch_predict_opdef),
    ]

    def get_operation(self, name, modeldef, parent_opdef):
        for p, handler in self.op_patterns:
            m = p.match(name)
            if m:
                return handler(name, modeldef, parent_opdef, *m.groups())
        return None

    def sync_run(self, run, options):
        from . import cloudml_op_main
        cloudml_op_main.sync_run(run, options.get("watch", False))

    def stop_run(self, run, options):
        from . import cloudml_op_main
        cloudml_op_main.stop_run(run, options.get("no_wait", False))
