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
from guild import model_proxy
from guild import plugin as pluginlib
from guild import python_util

class PythonScriptModelProxy(object):

    name = ""
    fullname = ""
    output_scalars = model_proxy.GENERIC_OUTPUT_SCALARS
    compare = model_proxy.GENERIC_COMPARE

    def __init__(self, op_name, script_path):
        assert script_path[-3:] == ".py", script_path
        self.op_name = op_name
        self.script_path = script_path
        self.modeldef = self._init_modeldef()
        self.reference = modellib.script_model_ref(self.name, script_path)

    def _init_modeldef(self):
        data = [
            {
                "model": self.name,
                "operations": {
                    self.op_name: {
                        "exec": self._exec_attr(),
                        "flags": self._flags_data(),
                        "compare": self.compare,
                        "output-scalars": self.output_scalars,
                    }
                },
                "disable-plugins": "all",
                "output-scalars": self.output_scalars,
            }
        ]
        gf = guildfile.Guildfile(data, dir=config.cwd())
        return gf.models[self.name]

    def _exec_attr(self):
        return (
            "${python_exe} -um guild.op_main %s ${flag_args}"
            % shlex_quote(self._script_module()))

    def _script_module(self):
        return python_util.script_module(self.script_path, config.cwd())

    def _flags_data(self):
        plugin = pluginlib.for_name("flags")
        return plugin.flags_data_for_path(self.script_path, ".")

class PythonScriptPlugin(pluginlib.Plugin):

    def guildfile_loaded(self, gf):
        for m in gf.models.values():
            for op in m.operations:
                if op.main or op.exec_ or op.steps:
                    continue
                if op.name.endswith(".py"):
                    op.main = op.name[:-3]

    @staticmethod
    def resolve_model_op(opspec):
        path = os.path.join(config.cwd(), opspec)
        if python_util.is_python_script(path):
            model = PythonScriptModelProxy(opspec, path)
            return model, model.op_name
        return None
