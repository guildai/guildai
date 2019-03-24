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
from guild import op_util
from guild import plugin as pluginlib
from guild import python_util

from .python_script import PythonScriptModelProxy
from .python_script import PythonScriptOpSupport

KERAS_OUTPUT_SCALARS = {
    "step": r"Epoch ([0-9]+)/[0-9]+",
    "loss": r"step - loss: ([0-9\.]+)",
    "acc": r"acc: ([0-9\.]+) - val_loss",
    "val_loss": r"val_loss: ([0-9\.]+)",
    "val_acc": r"val_acc: ([0-9\.]+)",
}

KERAS_BASE_COMPARE = [
    "loss step as step",
    "loss",
    "acc",
    "val_loss",
    "val_acc",
]

class KerasScriptModelProxy(PythonScriptModelProxy):

    output_scalars = KERAS_OUTPUT_SCALARS

    base_compare = KERAS_BASE_COMPARE

    objective = {
        "maximize": "val_acc"
    }

    disable_plugins = []

class KerasPlugin(pluginlib.Plugin, PythonScriptOpSupport):

    resolve_model_op_priority = 50

    def resolve_model_op(self, opspec):
        path = os.path.join(config.cwd(), opspec)
        if not python_util.is_python_script(path):
            return None
        script = python_util.Script(path)
        if not self.is_keras_script(script):
            return None
        model = KerasScriptModelProxy(opspec, script.src)
        return model, model.op_name

    def is_keras_script(self, script):
        return self._imports_keras(script) and self._op_method(script)

    @staticmethod
    def _imports_keras(script):
        return any(
            (name == "keras" or
             name.startswith("keras.") or
             name.startswith("tensorflow.keras"))
             for name in script.imports)

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

    def python_script_opdef(self, op):
        if (op.compare is not None and
            op.output_scalars is not None):
            return
        assert op.main, op
        plugin = pluginlib.for_name("python_script")
        main_mod = op_util.split_main(op.main)[0]
        model_paths = op_util.opdef_model_paths(op)
        try:
            _sys_path, mod_path = plugin.find_module(main_mod, model_paths)
        except ImportError:
            return
        script = python_util.Script(mod_path)
        if self.is_keras_script(script):
            if op.compare is None:
                flags = ["=%s" % f.name for f in op.flags]
                op.compare = flags + KERAS_BASE_COMPARE
            if op.output_scalars is None:
                op.output_scalars = KERAS_OUTPUT_SCALARS
