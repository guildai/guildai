# Copyright 2017-2020 TensorHub, Inc.
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
    r"Epoch (?P<step>[0-9]+)",
    r" - ([a-z_]+): (\value)",
    r"Test loss: (?P<test_loss>\value)",
    r"Test accuracy: (?P<test_accuracy>\value)",
]


class KerasScriptModelProxy(PythonScriptModelProxy):

    output_scalars = KERAS_OUTPUT_SCALARS

    plugins = ["summary"]


class KerasPlugin(pluginlib.Plugin, PythonScriptOpdefSupport):

    resolve_model_op_priority = 50

    def resolve_model_op(self, opspec):
        path = os.path.join(config.cwd(), opspec)
        if not python_util.is_python_script(path):
            self.log.debug("%s is not a python script", path)
            return None
        try:
            script = python_util.Script(path)
        except SyntaxError:
            return None
        else:
            if not self.is_keras_script(script):
                self.log.debug("%s is not a Keras script", path)
                return None
            model = KerasScriptModelProxy(script.src, opspec)
            self.log.debug("%s is a Keras script", path)
            return model, model.op_name

    def is_keras_script(self, script):
        imports_keras = self._imports_keras(script)
        op_method = self._op_method(script)
        return imports_keras and op_method

    @staticmethod
    def _imports_keras(script):
        imports = script.imports
        return any(
            (
                name == "keras"
                or name == "tensorflow"
                or name.startswith("keras.")
                or name.startswith("tensorflow.")
            )
            for name in imports
        )

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
        main_mod = op_util.split_cmd(opdef.main)[0]
        model_paths = op_util.opdef_model_paths(opdef)
        try:
            _path, mod_path = python_util.find_module(main_mod, model_paths)
        except ImportError:
            return
        try:
            script = python_util.Script(mod_path)
        except SyntaxError:
            return
        else:
            if self.is_keras_script(script):
                if opdef.output_scalars is None:
                    opdef.output_scalars = KERAS_OUTPUT_SCALARS
