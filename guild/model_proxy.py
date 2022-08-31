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

import logging

import guild

from guild import guildfile
from guild import model as modellib
from guild import plugin as pluginlib

log = logging.getLogger("guild")


class NotSupported(Exception):
    pass


class MissingRunOpdef(Exception):
    pass


class OpSpecError(Exception):
    pass


class BatchModelProxy:

    name = ""
    op_name = "+"
    op_description = "Default batch processor."
    module_name = "guild.batch_main"
    flag_encoder = None
    default_max_trials = None
    delete_on_success = True
    can_stage_trials = True
    flags_data = {}

    def __init__(self):
        self.modeldef = self._init_modeldef()
        self.reference = self._init_reference()

    def _init_modeldef(self):
        data = {
            "operations": {
                self.op_name: {
                    "description": self.op_description,
                    "exec": f"${{python_exe}} -um {self.module_name}",
                    "flag-encoder": self.flag_encoder,
                    "default-max-trials": self.default_max_trials,
                    "flags": self.flags_data,
                    "env": {
                        "NO_OP_INTERRUPTED_MSG": "1",
                    },
                    "delete-on-success": self.delete_on_success,
                    "can-stage-trials": self.can_stage_trials,
                }
            }
        }
        return modeldef(self.name, data, f"<{self.__class__.__name__}>")

    def _init_reference(self):
        return modellib.ModelRef("builtin", "guildai", guild.__version__, self.name)


def modeldef(model_name, model_data, src):
    model_data = dict(model_data)
    model_data["model"] = model_name
    gf_data = [model_data]
    gf = guildfile.Guildfile(gf_data, src=src)
    return gf.default_model


def resolve_model_op(opspec):
    if opspec == "+":
        model = BatchModelProxy()
        return model, model.op_name
    return resolve_plugin_model_op(opspec)


def resolve_plugin_model_op(opspec):
    for name, plugin in _plugins_by_resolve_model_op_priority():
        log.debug("resolving model op for %r with plugin %r", opspec, name)
        try:
            model_op = plugin.resolve_model_op(opspec)
        except pluginlib.ModelOpResolutionError as e:
            raise OpSpecError(e) from e
        else:
            if model_op:
                log.debug(
                    "got model op for %r from plugin %r: %s:%s",
                    opspec,
                    name,
                    model_op[0].name,
                    model_op[1],
                )
                return model_op
    raise NotSupported()


def _plugins_by_resolve_model_op_priority():
    return sorted(
        pluginlib.iter_plugins(), key=lambda x: x[1].resolve_model_op_priority
    )
