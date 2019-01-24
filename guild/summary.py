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

import re
import logging

log = logging.getLogger("guild")

class OutputScalars(object):

    def __init__(self, config, run):
        self._patterns, self._step_pattern = self._compile_patterns(config)
        self._run = run
        self._writer = None
        self._step = None

    @staticmethod
    def _compile_patterns(config):
        patterns = []
        step_pattern = None
        for key, val in sorted(config.items()):
            try:
                pattern = re.compile(val)
            except Exception as e:
                log.warning(
                    "error compiling pattern %s for "
                    "output scalar %s: %s", val, key, e)
            else:
                if pattern.groups != 1:
                    log.warning(
                        "pattern %s captures %i group(s), "
                        "expected 1 - skipping", val,
                        pattern.groups)
                    continue
                if key == "step":
                    step_pattern = pattern
                else:
                    patterns.append((key, pattern))
        return patterns, step_pattern

    def write(self, line):
        self._refresh_step(line)
        for key, pattern in self._patterns:
            val = self._try_float(pattern, line)
            if val is not None:
                writer = self._ensure_writer()
                writer.add_scalar(key, val, self._step)

    def _refresh_step(self, out):
        if self._step_pattern:
            maybe_step = self._try_int(self._step_pattern, out)
            if maybe_step:
                self._step = maybe_step

    def _try_float(self, pattern, s):
        return self._gen_try(pattern, s, float)

    def _try_int(self, pattern, s):
        return self._gen_try(pattern, s, int)

    @staticmethod
    def _gen_try(pattern, s, type_conv):
        m = pattern.search(s.decode())
        if not m:
            return None
        try:
            return type_conv(m.group(1))
        except ValueError:
            return None

    def _ensure_writer(self):
        import tensorboardX
        if self._writer is None:
            run_guild_dir = self._run.guild_path()
            self._writer = tensorboardX.SummaryWriter(run_guild_dir)
        return self._writer

    def close(self):
        if self._writer:
            self._writer.close()
