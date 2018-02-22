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

from guild import plugin
from guild.plugins import python_util

class KerasPlugin(plugin.Plugin):

    def find_models(self, path):
        return python_util.script_models(
            path, self._is_keras_script, self._script_model, self.log)

    def _is_keras_script(self, script):
        return self._imports_keras(script) and self._op_method(script)

    @staticmethod
    def _imports_keras(script):
        return any(
            (name == "keras" or name.startswith("keras.")
             for name in script.imports()))

    @staticmethod
    def _op_method(script):
        """Returns the first detected op method name.

        Op methods are inferred by calls to "fit" and "predict"
        functions. If a script contains one of these, we consider it
        an operation and return the method name.

        """
        op_methods = ["fit", "predict"]
        for call in script.calls():
            if call.name in op_methods:
                return call.name
        return None

    def _script_model(self, script):
        op_method = self._op_method(script)
        assert op_method, "should be caught in _is_keras_script"
        if op_method == "fit":
            return self._train_model(script)
        elif op_method == "predict":
            return self._predict_model(script)
        else:
            raise AssertionError(op_method)

    @staticmethod
    def _train_model(script):
        return {
            "name": script.name,
            "operations": {
                "train": {
                    "cmd": (
                        "guild.plugins.keras_op_main train %s" % script.src
                    ),
                    "description": "Train the model",
                    "flags": {
                        "epochs": {
                            "description": "Number of epochs to train"
                        },
                        "batch-size": {
                            "description": "Batch size per training step"
                        },
                        "datasets": {
                            "description": "Location of Keras datasets"
                        }
                    }
                }
            }
        }

    @staticmethod
    def _predict_model(script):
        return {
            "name": script.name,
            "operations": {
                "predict": {
                    "cmd": (
                        "guild.plugins.keras_op_main predict %s" % script.src
                    ),
                    "description": "Use a trained model to make a prediction"
                }
            }
        }
