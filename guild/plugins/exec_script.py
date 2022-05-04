# Copyright 2017-2022 RStudio, PBC
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

import os

from guild import config
from guild import guildfile
from guild import model as modellib
from guild import plugin
from guild import util


class ExecScriptModelProxy(object):
    def __init__(self, script_path, op_name):
        assert script_path.endswith(op_name), (script_path, op_name)
        self.script_path = script_path
        self.op_name = op_name
        self.name = ""
        self.fullname = ""
        self.modeldef = self._init_modeldef()
        script_base = script_path[: -len(op_name)]
        self.reference = modellib.script_model_ref(self.name, script_base)

    def _init_modeldef(self):
        abs_script = os.path.abspath(self.script_path)
        data = [
            {"model": self.name, "operations": {self.op_name: {"exec": abs_script}}}
        ]
        gf = guildfile.Guildfile(data, dir=os.path.dirname(abs_script))
        return gf.models[self.name]


class ExecScriptPlugin(plugin.Plugin):

    resolve_model_op_priority = 100

    def resolve_model_op(self, opspec):
        path = os.path.join(config.cwd(), opspec)
        if not os.path.exists(path):
            return None
        if not util.is_executable_file(path):
            raise plugin.ModelOpResolutionError("must be an executable file")
        model = ExecScriptModelProxy(path, opspec)
        return model, model.op_name
