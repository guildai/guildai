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
from guild import guildfile
from guild import op_util
from guild import util

from guild.plugin import Plugin

class FlagsPlugin(Plugin):

    def guildfile_loaded(self, gf):
        cache = {}
        for m in gf.models.values():
            for opdef in m.operations:
                try:
                    imports = opdef.flags_special["$import"]
                except KeyError:
                    continue
                imported_data = self._flags_data(imports, opdef, cache)
                self._apply_imported_flags_data(imported_data, opdef)

    def _flags_data(self, imports, opdef, cache):
        main_mod = op_util.split_main(opdef.main)[0]
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

    def _apply_imported_flags_data(self, imported_data, opdef):
        for name, data in imported_data.items():
            existing = opdef.get_flagdef(name)
            if existing:
                self._apply_imported_flag_data(data, existing)
            else:
                opdef.flags.append(guildfile.FlagDef(name, data, opdef))
        opdef.flags.sort(key=lambda f: f.name)

    @staticmethod
    def _apply_imported_flag_data(data, flag):
        if flag.default is None:
            flag.default = data.get("default")
        if not flag.description:
            flag.description = data.get("description", "")
