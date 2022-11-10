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

from guild.plugins.summary_util import SummaryPlugin


class CPUPlugin(SummaryPlugin):
    def __init__(self, ep):
        super().__init__(ep)
        self._cpu_percent_init = False

    def enabled_for_op(self, _opdef):
        try:
            import psutil as _unused
        except ImportError as e:
            self.log.warning(
                "cpu stats disabled because psutil cannot be imported (%s)", e
            )
            return False, f"error importing psutil: {e}"
        else:
            return True, "psutil available"

    def read_summary_values(self, _step):
        return self._cpu_stats()

    def _cpu_stats(self):
        import psutil

        percents = psutil.cpu_percent(None, True)
        stats = {}
        if self._cpu_percent_init:
            i = 0
            for percent in percents:
                stats[f"sys/cpu{i}/util"] = percent / 100
                i += 1
            if percents:
                stats["sys/cpu/util"] = sum(percents) / len(percents) / 100
        self._cpu_percent_init = True
        return stats
