# Copyright 2017-2018 TensorHub, Inc.
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

import json
import os
import subprocess
import sys

from guild import config
from guild import op_util
from guild import util

from guild.plugin import Plugin

class FlagsPlugin(Plugin):

    def guildfile_data(self, data, _src):
        cache = {}
        for op_data in self._iter_ops_with_flags(data):
            try:
                flags_import = op_data["flags"].pop("$import")
            except KeyError:
                continue
            else:
                self._try_apply_imports(flags_import, op_data, cache)

    def _iter_ops_with_flags(self, data):
        if not isinstance(data, list):
            data = [data]
        for top_level in data:
            for op_data in self._iter_ops_with_flags_recurse(top_level):
                yield op_data

    def _iter_ops_with_flags_recurse(self, data):
        if isinstance(data, dict):
            for name, val in sorted(data.items()):
                if name == "operations" and isinstance(val, dict):
                    for _, op_data in sorted(val.items()):
                        if isinstance(op_data, dict) and "flags" in op_data:
                            yield op_data
                else:
                    for op_data in self._iter_ops_with_flags_recurse(val):
                        yield op_data

    def _try_apply_imports(self, flags_import, op_data, cache):
        import_data = self._import_data(flags_import, op_data, cache)
        if import_data:
            self._apply_import_data(import_data, op_data)

    def _import_data(self, imports, op_data, cache):
        main_mod = op_util.split_main(op_data.get("main"))[0]
        try:
            flags_data = cache[main_mod]
        except KeyError:
            flags_data = self._load_flags_data(main_mod)
            cache[main_mod] = flags_data
        return self._filter_flags(flags_data, imports)

    def _load_flags_data(self, main_mod):
        env = {
            "PYTHONPATH": os.path.pathsep.join(sys.path),
            "GUILD_CWD": config.cwd(),
            "LOG_LEVEL": str(self.log.getEffectiveLevel())
        }
        with util.TempFile() as data_path:
            cmd = [
                sys.executable,
                "-m", "guild.plugins.import_flags_main",
                main_mod, data_path]
            try:
                subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env)
            except subprocess.CalledProcessError as e:
                self.log.warning(
                    "cannot import flags from %s: %s",
                    main_mod, e.output.decode().strip())
                return {}
            else:
                return self._load_data(data_path)

    @staticmethod
    def _load_data(path):
        out = open(path, "r").read().strip()
        if not out:
            return {}
        return json.loads(out)

    @staticmethod
    def _filter_flags(data, imports):
        return {
            name: data[name] for name in data if name in imports
        }

    def _apply_import_data(self, flag_import_data, op_data):
        for flag_name, flag_data in flag_import_data.items():
            op_flags = op_data["flags"]
            try:
                op_flag_data = op_flags[flag_name]
            except KeyError:
                op_flags[flag_name] = flag_data
            else:
                if not isinstance(op_flag_data, dict):
                    # Coerce default value to full data
                    op_flag_data = {"default": op_flag_data}
                    op_flags[flag_name] = op_flag_data
                self._apply_import_flag(flag_data, op_flag_data)

    @staticmethod
    def _coerce_flag_data(data):
        if isinstance(data, dict):
            return data
        return {"default": data}

    @staticmethod
    def _apply_import_flag(flag_import_data, op_flag_data):
        for name, val in flag_import_data.items():
            if name not in op_flag_data:
                op_flag_data[name] = val
