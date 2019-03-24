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

import hashlib
import imp
import json
import os
import subprocess
import sys
import yaml

import six

from six.moves import shlex_quote

from guild import cli
from guild import config
from guild import guildfile
from guild import model as modellib
from guild import model_proxy
from guild import op_util
from guild import plugin as pluginlib
from guild import python_util
from guild import util
from guild import var

IMPLICIT_ALL_FLAGS = object()

class DataLoadError(Exception):
    pass

class PythonScriptOpSupport(object):
    """Interface for Python script op support.

    `python_script_op` is called to potentially update op.
    """

    def python_script_opdef(self, opdef):
        pass

class PythonScriptModelProxy(object):

    name = ""
    fullname = ""
    output_scalars = model_proxy.GENERIC_OUTPUT_SCALARS
    base_compare = ["loss"]
    objective = "loss"
    disable_plugins = "all"

    def __init__(self, op_name, script_path):
        assert script_path[-3:] == ".py", script_path
        self.op_name = op_name
        self.script_path = script_path
        self.modeldef = self._init_modeldef()
        self.reference = modellib.script_model_ref(self.name, script_path)

    def _init_modeldef(self):
        flags_data = self._flags_data()
        flags_dest = flags_data.pop("$dest", None)
        data = [
            {
                "model": self.name,
                "operations": {
                    self.op_name: {
                        "exec": self._exec_attr(),
                        "flags": flags_data,
                        "flags-dest": flags_dest,
                        "compare": self._compare(flags_data),
                        "output-scalars": self.output_scalars,
                        "objective": self.objective,
                        "disable-plugins": self.disable_plugins,
                    }
                }
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
        plugin = pluginlib.for_name("python_script")
        return plugin.flags_data_for_path(self.script_path, ".")

    def _compare(self, flags_data):
        flags = [
            "=%s" % name
            for name in sorted(flags_data)
            if name[:1] != "$"]
        return flags + self.base_compare

class ImportedFlagsOpProxy(object):

    def __init__(self, flags_data, real_op, log):
        self.guildfile = real_op.guildfile
        self.flags = self._init_flags(flags_data, real_op.main, log)

    def _init_flags(self, flags_data, main_mod, log):
        flags = []
        for name, flag_data in flags_data.items():
            try:
                flag_data = guildfile.coerce_flag_data(
                    name, flag_data, self.guildfile)
            except guildfile.GuildfileError as e:
                log.warning("cannot import flags from %s: %s", main_mod, e)
            else:
                flags.append(guildfile.FlagDef(name, flag_data, self))
        return flags

    def flag_values(self):
        return {f.name: f.default for f in self.flags}

class PythonScriptPlugin(pluginlib.Plugin):

    def resolve_model_op(self, opspec):
        path = os.path.join(config.cwd(), opspec)
        if not python_util.is_python_script(path):
            return None
        model = PythonScriptModelProxy(opspec, path)
        return model, model.op_name

    def guildfile_loaded(self, gf):
        for m in gf.models.values():
            for op in m.operations:
                self._maybe_apply_main(op)
                if op.main:
                    self._apply_script_flags(op)
                    self._notify_plugins_opdef(op)

    @staticmethod
    def _maybe_apply_main(op):
        if not (op.main is not None or
                op.exec_ is not None or
                op.steps is not None):
            op.main = python_util.safe_module_name(op.name)

    def _apply_script_flags(self, op):
        if op.flags_import in ([], False):
            return
        local_cache = {}
        model_paths = op_util.opdef_model_paths(op)
        flags_data = self._flags_data(op.main, model_paths, local_cache)
        op.flags_dest = flags_data.pop("$dest", None)
        import_data = {
            name: flags_data[name]
            for name in flags_data
            if op.flags_import is None or name in op.flags_import
        }
        op.merge_flags(ImportedFlagsOpProxy(import_data, op, self.log))

    def _flags_data(self, main, model_paths, local_cache):
        main_mod = op_util.split_main(main)[0]
        try:
            flags_data = local_cache[main_mod]
        except KeyError:
            flags_data = self._flags_data_(main_mod, model_paths)
            local_cache[main_mod] = flags_data
        return flags_data

    def _flags_data_(self, main_mod, model_paths):
        try:
            sys_path, mod_path = self.find_module(main_mod, model_paths)
        except ImportError as e:
            self.log.warning("cannot import flags from %s: %s", main_mod, e)
            return {}
        else:
            return self.flags_data_for_path(mod_path, sys_path)

    def find_module(self, main_mod, model_paths):
        for model_path in model_paths:
            main_mod_sys_path, module = self._split_module(main_mod, model_path)
            # Copied from guild.op_main
            parts = module.split(".")
            module_path = parts[0:-1]
            module_name_part = parts[-1]
            for sys_path_item in [main_mod_sys_path] + sys.path:
                cur_path = os.path.join(sys_path_item, *module_path)
                try:
                    mod_info = imp.find_module(module_name_part, [cur_path])
                except ImportError:
                    pass
                else:
                    _f, found_path, _desc = mod_info
                    # Don't attempt to import flags from anything other
                    # than a file ending in '.py'
                    if os.path.isfile(found_path) and found_path.endswith(".py"):
                        return main_mod_sys_path, found_path
        raise ImportError("No module named %s" % main_mod)

    @staticmethod
    def _split_module(main_mod, gf_dir):
        parts = main_mod.rsplit("/", 1)
        if len(parts) == 1:
            parts = ".", parts[0]
        return os.path.join(gf_dir, parts[0]), parts[1]

    def flags_data_for_path(self, mod_path, sys_path):
        data, cached_data_path = self._cached_data(mod_path)
        if data is not None:
            return data
        return self._load_and_cache_flags_data(
            mod_path, sys_path, cached_data_path)

    def _cached_data(self, mod_path):
        cached_path = self._cached_data_path(mod_path)
        if self._cache_valid(cached_path, mod_path):
            with open(cached_path, "r") as f:
                # Use yaml to avoid json's insistence on treating
                # strings as unicode.
                return yaml.safe_load(f), cached_path
        return None, cached_path

    @staticmethod
    def _cached_data_path(mod_path):
        cache_dir = var.cache_dir("import-flags")
        abs_path = os.path.abspath(mod_path)
        path_hash = hashlib.md5(abs_path.encode()).hexdigest()
        return os.path.join(cache_dir, path_hash)

    @staticmethod
    def _cache_valid(cache_path, mod_path):
        if not os.path.exists(cache_path):
            return False
        return os.path.getmtime(mod_path) <= os.path.getmtime(cache_path)

    def _load_and_cache_flags_data(self, mod_path, sys_path, cached_data_path):
        if os.getenv("NO_IMPORT_FLAGS_PROGRESS") != "1":
            cli.note_once("Refreshing project info...")
        script = python_util.Script(mod_path)
        try:
            data = self._flags_data_for_script(script, mod_path, sys_path)
        except DataLoadError:
            return {}
        else:
            self._apply_abs_paths(data, os.path.dirname(script.src))
            self._cache_data(data, cached_data_path)
            return data

    @staticmethod
    def _cache_data(data, path):
        util.ensure_dir(os.path.dirname(path))
        with open(path, "w") as f:
            json.dump(data, f)

    def _flags_data_for_script(self, script, mod_path, sys_path):
        if self._imports_argparse(script):
            data = self._load_argparse_flags_data(mod_path, sys_path)
            data["$dest"] = "args"
        else:
            data = self._global_assigns_flags_data(script)
            data["$dest"] = "globals"
        return data

    @staticmethod
    def _imports_argparse(script):
        return "argparse" in script.imports

    def _load_argparse_flags_data(self, mod_path, sys_path):
        env = dict(os.environ)
        env.update({
            "PYTHONPATH": os.path.pathsep.join([sys_path] + sys.path),
            "LOG_LEVEL": str(self.log.getEffectiveLevel()),
        })
        with util.TempFile() as data_path:
            cmd = [
                sys.executable,
                "-m", "guild.plugins.import_argparse_flags_main",
                mod_path, data_path]
            self.log.debug("import_argparse_flags_main env: %s", env)
            self.log.debug("import_argparse_flags_main cmd: %s", cmd)
            try:
                out = subprocess.check_output(
                    cmd, stderr=subprocess.STDOUT, env=env)
            except subprocess.CalledProcessError as e:
                self.log.warning(
                    "cannot import flags from %s: %s",
                    mod_path, e.output.decode().strip())
                raise DataLoadError()
            else:
                self.log.debug("import_argparse_flags_main output: %s", out)
                return self._load_data(data_path)

    @staticmethod
    def _load_data(path):
        out = open(path, "r").read().strip()
        if not out:
            return {}
        return yaml.safe_load(out)

    def _global_assigns_flags_data(self, script):
        return self._public_params(script.params)

    @staticmethod
    def _public_params(params):
        return {
            str(name): params[name] for name in params
            if name[:1] != "_"
        }

    @staticmethod
    def _apply_abs_paths(data, script_dir):
        for flag_data in data.values():
            if not isinstance(flag_data, dict):
                continue
            default = flag_data.get("default")
            if (not default or
                not isinstance(default, six.string_types) or
                os.path.sep not in default):
                continue
            abs_path = os.path.join(script_dir, default)
            if os.path.exists(abs_path):
                flag_data["default"] = abs_path

    @staticmethod
    def _notify_plugins_opdef(opdef):
        for _name, plugin in pluginlib.iter_plugins():
            if isinstance(plugin, PythonScriptOpSupport):
                plugin.python_script_opdef(opdef)
