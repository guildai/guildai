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
from guild import model as modellib
from guild import plugin
from guild import util

class ExecScriptModelProxy(object):

    def __init__(self, op_name, script_path):
        self.op_name = op_name
        self.script_path = script_path
        self.name = ""
        self.fullname = ""
        self.modeldef = self._init_modeldef()
        self.reference = modellib.script_model_ref(self.name, script_path)

    def _init_modeldef(self):
        abs_script = os.path.abspath(self.script_path)
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
        gf = guildfile.Guildfile(data, dir=os.path.dirname(abs_script))
        return gf.models[self.name]

class ExecScriptPlugin(plugin.Plugin):

    @staticmethod
    def resolve_model_op(opspec):
        path = os.path.join(config.cwd(), opspec)
        if util.is_executable_file(path):
            model = ExecScriptModelProxy(opspec, path)
            return model, model.op_name
        return None
