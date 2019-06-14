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
from .python_script import PythonScriptOpdefSupport

KERAS_OUTPUT_SCALARS = [
    r"Epoch (?P<step>[0-9]+)/",
    r" - ([a-z_]+): ([0-9\.e\-]+)"
]

class KerasScriptModelProxy(PythonScriptModelProxy):

    output_scalars = KERAS_OUTPUT_SCALARS

    objective = {
        "maximize": "val_acc"
    }

    disable_plugins = []

class KerasPlugin(pluginlib.Plugin, PythonScriptOpdefSupport):

    resolve_model_op_priority = 50

    def resolve_model_op(self, opspec):
        path = os.path.join(config.cwd(), opspec)
        if not python_util.is_python_script(path):
            self.log.debug("%s is not a python script", path)
            return None
        script = python_util.Script(path)
        if not self.is_keras_script(script):
            self.log.debug("%s is not a Keras script", path)
            return None
        model = KerasScriptModelProxy(opspec, script.src)
        self.log.debug("%s is a Keras script", path)
        return model, model.op_name

    def is_keras_script(self, script):
        imports_keras = self._imports_keras(script)
        op_method = self._op_method(script)
        self.log.debug(
            "%s imports keras = %s, op_method = %s",
            script.src, imports_keras,
            op_method.name if op_method else "None")
        return imports_keras and op_method

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

    def python_script_opdef_loaded(self, opdef):
        if opdef.output_scalars is not None:
            return
        assert opdef.main, opdef
        plugin = pluginlib.for_name("python_script")
        main_mod = op_util.split_main(opdef.main)[0]
        model_paths = op_util.opdef_model_paths(opdef)
        try:
            _sys_path, mod_path = plugin.find_module(main_mod, model_paths)
        except ImportError:
            return
        script = python_util.Script(mod_path)
        if self.is_keras_script(script):
            if opdef.output_scalars is None:
                opdef.output_scalars = KERAS_OUTPUT_SCALARS
