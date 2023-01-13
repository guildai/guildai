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
import sys
import platform
import shlex

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


class ModelProxy:
    """Stub for a model proxy.

    Used to document required attributes but otherwise does not
    provide a proxy facility.
    """

    # Requires attributes - generally configured in `__init__()`
    name = None
    modeldef = None
    reference = None


def _sys_executable():
    exe = sys.executable
    if platform.system() != "Windows" and " " in exe:
        exe = shlex.quote(exe)
    # If this runtime was invoked with a "-I" python cli arg,
    # pass it through to subprocesses that also launch guild internal modules.
    # A "-I" python cli flag is used by the R plugin to invoke guild on some platforms.
    # Other flags we may want to pass through: https://docs.python.org/3/library/sys.html#sys.flags
    if sys.flags.isolated:
        exe += " -I"
    return exe


class DefaultBatchModelProxy:
    def __init__(self):
        self.name = ""
        self.reference = modellib.ModelRef(
            "builtin",
            "guildai",
            guild.__version__,
            self.name,
        )
        self.modeldef = modeldef(
            self.name,
            {
                "operations": {
                    "+": {
                        "description": "Default batch processor.",
                        "exec": f"{_sys_executable()} -um guild.batch_main",
                        "env": {
                            "NO_OP_INTERRUPTED_MSG": "1",
                        },
                        "delete-on-success": True,
                        "can-stage-trials": True,
                        "pip-freeze": False,
                    }
                }
            },
            f"<{self.__class__.__name__}>",
        )


def modeldef(model_name, model_data, src=None, dir=None):
    assert src or dir, "either src or dir is required"
    model_data = dict(model_data)
    model_data["model"] = model_name
    gf_data = [model_data]
    gf = guildfile.Guildfile(gf_data, src=src, dir=dir)
    return gf.default_model


def resolve_model_op(opspec):
    return _builtin_model_op_for_spec(opspec) or resolve_plugin_model_op(opspec)


def _builtin_model_op_for_spec(opspec):
    if opspec == "+":
        return DefaultBatchModelProxy(), "+"
    return None


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
