# Copyright 2017-2023 Posit Software, PBC
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
import os

import yaml

import guild

from guild import config
from guild import guildfile
from guild import model as modellib
from guild import model_proxy
from guild import plugin as pluginlib

from . import r_util

log = logging.getLogger("guild")


class RScriptBuiltinsModelProxy:
    def __init__(self):
        self.name = "r-script"
        self.reference = modellib.ModelRef(
            "builtin",
            "guildai",
            guild.__version__,
            self.name,
        )
        self.modeldef = model_proxy.modeldef(
            self.name,
            {
                "operations": {
                    "init": {
                        "description": "Initialize R script support for Guild.",
                        "main": "guild.plugins.r_script_init_main",
                    }
                }
            },
            f"<{self.__class__.__name__}>",
        )


class RScriptModelProxy:
    name = ""
    output_scalars = None
    objective = "loss"
    plugins = None

    def __init__(self, script_path, op_name):
        assert script_path[-2:].upper() == ".R", script_path
        assert script_path.endswith(op_name), (script_path, op_name)
        self.script_path = script_path
        if os.path.isabs(op_name) or op_name.startswith(".."):
            self.op_name = os.path.basename(op_name)
        else:
            self.op_name = op_name
        script_base = script_path[:-len(self.op_name)]
        self.reference = modellib.script_model_ref(self.name, script_base)
        guildfile_dir, _rel_script_path = guildfile.split_script_path(script_path)
        self.modeldef = model_proxy.modeldef(
            self.name,
            {"operations": {
                self.op_name: _op_data_for_script(script_path),
            }},
            dir=guildfile_dir,
        )
        _apply_config_flags(self.modeldef, self.op_name)


def _apply_config_flags(modeldef, op_name):
    from . import config_flags

    opdef = modeldef.get_operation(op_name)
    config_flags.apply_config_flags(opdef)


class RScriptPlugin(pluginlib.Plugin):
    resolve_model_op_priority = 60

    def resolve_model_op(self, opspec):
        """Return a tuple of model, op_name for opspec.

        If opspec cannot be resolved to an R based operation, returns
        None.
        """
        if opspec == "r-script:init":
            return _r_script_init_model_op()
        path = _path_for_opspec(opspec)
        if not r_util.is_r_script(path):
            return None
        try:
            r_util.verify_r_env()
        except r_util.REnvError as e:
            raise pluginlib.ModelOpResolutionError(e)
        else:
            model = RScriptModelProxy(path, opspec)
            return model, model.op_name

    def enabled_for_op(self, opdef):
        if r_util.is_r_script(opdef.name):
            return True, "operation is an R script"
        return False, "operation is not an R script"

    def guildfile_loaded(self, gf):
        """Called immediately after a Guild file is loaded.

        If op config for an R op is defined in guild.yml, this
        augments that OpDef with r script guild data
        (i.e., flags, user supplied hashpipe yaml frontmatter)
        """
        for m in gf.models.values():
            for i, opdef in enumerate(m.operations):
                if not r_util.is_r_script(opdef.name):
                    continue

                script_data = _op_data_for_script(opdef.name)
                guildfile_data = opdef._data

                # build up the new data by merging the two dicts
                # config in the script frontmatter takes precedence
                data = guildfile_data.copy()
                data.update(script_data)

                # TODO: merge select rules, other custom logic to be implemented
                if "sourcecode" in guildfile_data and "sourcecode" in script_data:
                    # data['sourcecode'] = ...
                    pass

                # replace the opdef with a new one built from the merged data dict
                m.operations[i] = guildfile.OpDef(opdef.name, data, m)


def _r_script_init_model_op():
    return RScriptBuiltinsModelProxy(), "init"


def _path_for_opspec(opspec):
    if opspec.startswith(("/", "./")) and os.path.isfile(opspec):
        return opspec
    return os.path.join(config.cwd(), opspec)


def _op_data_for_script(r_script_path):
    try:
        out = r_util.run_r("guildai:::emit_r_script_guild_data()", args=[r_script_path])
    except r_util.RScriptProcessError as e:
        log.warning(e.output.rstrip().decode("utf-8"))
        return {}
    else:
        return yaml.safe_load(out)


def merge_dicts(dict1, dict2):
    """Recursively merges dict2 into dict1. Modifies dict1 in place"""
    for k in dict2:
        if k in dict1:
            dict1[k] = merge_dicts(dict1[k], dict2[k])
        else:
            dict1[k] = dict2[k]
    return dict1
