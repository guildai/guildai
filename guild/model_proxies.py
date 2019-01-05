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

from six.moves import shlex_quote

from guild import config
from guild import guildfile
from guild import model as modellib
from guild import plugin as plugins
from guild import python_util

GENERIC_COMPARE = [
    # step
    "loss step as step",

    # loss
    "loss",

    # accuracy
    "acc",
    "accuracy as acc",

    # val loss
    "val_loss",
    "val#loss as val_loss",

    # val acc
    "val_acc",
    "val#acc as val_acc",
]

class NotSupported(Exception):
    pass

class PythonScriptModelProxy(object):

    def __init__(self, script_path):
        assert script_path[-3:] == ".py", script_path
        self.script_path = script_path
        self.name = ""
        self.fullname = ""
        self.op_name = os.path.basename(script_path)
        self.modeldef = self._init_modeldef()
        self.reference = self._init_reference()

    def _init_modeldef(self):
        data = [
            {
                "model": self.name,
                "operations": {
                    self.op_name: {
                        "exec": self._exec_attr(),
                        "compare": GENERIC_COMPARE
                    }
                }
            }
        ]
        gf = guildfile.Guildfile(data, dir=config.cwd())
        modeldef = gf.models[self.name]
        self._patch_opref(modeldef.get_operation(self.op_name))
        return modeldef

    def _exec_attr(self):
        abs_script_path = os.path.abspath(self.script_path)
        return (
            "${python_exe} -u %s ${flag_args}"
            % shlex_quote(abs_script_path))

    def _patch_opref(self, opref):
        """Patches opref so that it always returns a flag def.

        This allows flag checks to pass - any flags provided to run are
        accepted.
        """
        opref.get_flagdef = lambda _: self._flagdef_proxy()

    class _flagdef_proxy(object):
        arg_name = None
        arg_skip = False
        arg_switch = None
        choices = None
        name = None
        type = None

    def _init_reference(self):
        return modellib.ModelRef(
            "script",
            self.script_path,
            modellib.file_hash(self.script_path),
            self.name)

class KerasScriptModelProxy(PythonScriptModelProxy):

    def __init__(self, script):
        self._script = script
        super(KerasScriptModelProxy, self).__init__(script.src)

    def _init_modeldef(self):
        plugin = plugins.for_name("keras")
        data = plugin.script_model(self._script)
        self._rename_model_and_op(data)
        gf = guildfile.Guildfile(data, dir=config.cwd())
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

def resolve_model_op(opspec):
    if _is_python_script(opspec):
        model = _python_script_model(opspec)
        return model, model.op_name
    raise NotSupported()

def _is_python_script(opspec):
    return os.path.isfile(opspec) and opspec[-3:] == ".py"

def _python_script_model(opspec):
    script = python_util.Script(opspec)
    if _is_keras_script(script):
        return KerasScriptModelProxy(script)
    return PythonScriptModelProxy(opspec)

def _is_keras_script(script):
    plugin = plugins.for_name("keras")
    return plugin.is_keras_script(script)
