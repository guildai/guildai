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

import logging

import guild

from guild import config
from guild import guildfile
from guild import model as modellib
from guild import plugin as pluginlib

log = logging.getLogger("guild")

GENERIC_OUTPUT_SCALARS = {
    "step": r"step:\s*(\S+)",
    "loss": r"loss:\s*(\S+)",
}

class NotSupported(Exception):
    pass

class BatchModelProxy(object):

    name = ""
    op_name = "+"
    op_description = "Default batch processor."
    module_name = "guild.batch_main"
    flag_encoder = None
    default_max_trials = 20
    flags_data = {}

    def __init__(self):
        self.modeldef = self._init_modeldef()
        self.reference = self._init_reference()

    def _init_modeldef(self):
        data = [
            {
                "model": self.name,
                "operations": {
                    self.op_name: {
                        "description": self.op_description,
                        "exec": "${python_exe} -um %s" % self.module_name,
                        "flag-encoder": self.flag_encoder,
                        "default-max-trials": self.default_max_trials,
                        "flags": self.flags_data,
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

def resolve_model_op(opspec):
    if opspec == "+":
        model = BatchModelProxy()
        return model, model.op_name
    return _resolve_plugin_model_op(opspec)

def _resolve_plugin_model_op(opspec):
    for name, plugin in _plugins_by_resolve_model_op_priority():
        log.debug("resolving model op for %r with plugin %r", opspec, name)
        model_op = plugin.resolve_model_op(opspec)
        if model_op:
            log.debug(
                "got model op for %r from plugin %r: %s:%s",
                opspec, name, model_op[0].name, model_op[1])
            return model_op
    raise NotSupported()

def _plugins_by_resolve_model_op_priority():
    return sorted(
        pluginlib.iter_plugins(),
        key=lambda x: x[1].resolve_model_op_priority)
