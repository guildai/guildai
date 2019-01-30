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

import os

from guild import config
from guild import guildfile
from guild import plugin as pluginlib
from guild import python_util

from .python_script import PythonScriptModelProxy

class KerasScriptModelProxy(PythonScriptModelProxy):

    # Assuming Keras plugin installs TensorBoard callback, which
    # collets scalars
    #
    output_scalars = None

    def __init__(self, op_name, script):
        self._script = script
        super(KerasScriptModelProxy, self).__init__(op_name, script.src)

    def _init_modeldef(self):
        plugin = pluginlib.for_name("keras")
        model_data = plugin.script_model(self._script)
        self._rename_model_and_op(model_data)
        self._reenable_plugins(model_data)
        gf = guildfile.Guildfile([model_data], dir=config.cwd())
        return gf.models[self.name]

    def _rename_model_and_op(self, data):
        """Rename model and op in data provided by Keras plugin.

        The Keras plugin uses the script name for the model and
        'train' for the operation. We want to make sure our model is
        named `self.name` and has an operation named `self.op_name`.
        """
        assert "model" in data, data
        assert "train" in data.get("operations", {}), data
        data["model"] = self.name
        data["operations"][self.op_name] = data["operations"].pop("train")

    @staticmethod
    def _reenable_plugins(data):
        data.pop("disable-plugins", None)

class KerasPlugin(pluginlib.Plugin):

    resolve_model_op_priority = 50

    def resolve_model_op(self, opspec):
        path = os.path.join(config.cwd(), opspec)
        if not python_util.is_python_script(path):
            return None
        script = python_util.Script(path)
        if not self.is_keras_script(script):
            return None
        model = KerasScriptModelProxy(opspec, script)
        return model, model.op_name

    def is_keras_script(self, script):
        return self._imports_keras(script) and self._op_method(script)

    @staticmethod
    def _imports_keras(script):
        return any(
            (name == "keras" or name.startswith("keras.")
             for name in script.imports))

    @staticmethod
    def _op_method(script):
        """Returns the last method of fit or predict.

        If fit is called, the last call is always returned, regardless
        of whether predict is called.

        """
        predict = None
        for call in reversed(script.calls):
            if call.name == "fit":
                return call
            elif call.name == "predict":
                predict = call
        return predict

    def script_model(self, script):
        op_method = self._op_method(script)
        assert op_method, "should be caught in is_keras_script"
        if op_method.name == "fit":
            return self._train_model(script, op_method)
        elif op_method.name == "predict":
            return self._predict_model(script)
        else:
            raise AssertionError(op_method)

    def _train_model(self, script, fit):
        return {
            "model": script.name,
            "operations": {
                "train": {
                    "main": (
                        "guild.plugins.keras_op_main train %s" % script.src
                    ),
                    "description": "Train the model",
                    "flags": {
                        "epochs": {
                            "description": "Number of epochs to train",
                            "default": self._default_epochs(script, fit)
                        },
                        "batch_size": {
                            "description": "Batch size per training step",
                            "default": self._default_batch_size(script, fit)
                        },
                        "datasets": {
                            "description": "Location of Keras datasets"
                        }
                    },
                    "compare": [
                        "loss step as step",
                        "loss as loss",
                        "acc as acc",
                        "val_loss as val_loss",
                        "val_acc as val_acc",
                    ]
                }
            }
        }

    @staticmethod
    def _default_epochs(script, fit):
        return (
            fit.kwarg_param("epochs") or
            script.params.get("epochs") or
            script.params.get("EPOCHS")
        )

    @staticmethod
    def _default_batch_size(script, fit):
        return (
            fit.kwarg_param("batch_size") or
            script.params.get("batch_size") or
            script.params.get("BATCH_SIZE")
        )

    @staticmethod
    def _predict_model(script):
        return {
            "model": script.name,
            "operations": {
                "predict": {
                    "main": (
                        "guild.plugins.keras_op_main predict %s" % script.src
                    ),
                    "description": "Use a trained model to make a prediction"
                }
            }
        }
