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

import guild

from guild import config
from guild import guildfile
from guild import model as modellib
from guild import plugin as plugins
from guild import python_util
from guild import util

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

class BatchModelProxy(object):

    def __init__(self):
        self.name = ""
        self.op_name = "+"
        self.modeldef = self._init_modeldef()
        self.reference = self._init_reference()

    def _init_modeldef(self):
        data = [
            {
                "model": self.name,
                "operations": {
                    self.op_name: {
                        "exec": "${python_exe} -um guild.batch_main"
                    }
                }
            }
        ]
        gf = guildfile.Guildfile(data, dir=config.cwd())
        return gf.models[self.name]

    def _init_reference(self):
        return modellib.ModelRef(
            "builtin",
            "guildai",
            guild.__version__,
            self.name)

class PythonScriptModelProxy(object):

    def __init__(self, script):
        assert script[-3:] == ".py", script
        self.script = script
        self.name = ""
        self.fullname = ""
        self.op_name = os.path.basename(script)
        self.modeldef = self._init_modeldef()
        self.reference = _script_model_reference(self.name, script)

    def _init_modeldef(self):
        data = [
            {
                "model": self.name,
                "operations": {
                    self.op_name: {
                        "exec": self._exec_attr(),
                        "compare": GENERIC_COMPARE,
                        "flags": self._flags_data(),
                    }
                }
            }
        ]
        gf = guildfile.Guildfile(data, dir=config.cwd())
        return gf.models[self.name]

    def _exec_attr(self):
        abs_script = os.path.abspath(self.script)
        return (
            "${python_exe} -u %s ${flag_args}"
            % shlex_quote(abs_script))

    def _flags_data(self):
        plugin = plugins.for_name("flags")
        return plugin._flags_data_for_path(self.script, ".")

class KerasScriptModelProxy(PythonScriptModelProxy):

    def __init__(self, script):
        self._script = script
        super(KerasScriptModelProxy, self).__init__(script.src)

    def _init_modeldef(self):
        plugin = plugins.for_name("keras")
        model_data = plugin.script_model(self._script)
        self._rename_model_and_op(model_data)
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

class ExecScriptModelProxy(object):

    def __init__(self, script):
        self.script = script
        self.name = ""
        self.fullname = ""
        self.op_name = script
        self.modeldef = self._init_modeldef()
        self.reference = _script_model_reference(self.name, script)

    def _init_modeldef(self):
        abs_script = os.path.abspath(self.script)
        data = [
            {
                "model": self.name,
                "operations": {
                    self.op_name: {
                        "exec": abs_script
                    }
                }
            }
        ]
        gf = guildfile.Guildfile(data, dir=config.cwd())
        return gf.models[self.name]

def _script_model_reference(model_name, script):
    script_abs_path = os.path.abspath(os.path.join(config.cwd(), script))
    return modellib.ModelRef(
        "script",
        script_abs_path,
        modellib.file_hash(script),
        model_name)

def resolve_model_op(opspec):
    if opspec == "+":
        model = BatchModelProxy()
        return model, model.op_name
    elif _is_python_script(opspec):
        model = _python_script_model(opspec)
        return model, model.op_name
    elif util.is_executable_file(opspec):
        model = ExecScriptModelProxy(opspec)
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
