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

from guild import plugin
from guild import python_util

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

    def _script_model(self, script):
        op_method = self._op_method(script)
        assert op_method, "should be caught in _is_keras_script"
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
                        "batch-size": {
                            "description": "Batch size per training step",
                            "default": self._default_batch_size(script, fit)
                        },
                        "datasets": {
                            "description": "Location of Keras datasets"
                        }
                    }
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
