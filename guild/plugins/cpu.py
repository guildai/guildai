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

from guild.plugins.tensorflow_util import SummaryPlugin

class CPUPlugin(SummaryPlugin):

    def __init__(self, ep):
        super(CPUPlugin, self).__init__(ep)
        self._cpu_percent_init = False

    def enabled_for_op(self, _op):
        return True, ""

    def read_summary_values(self, _step):
        return self._cpu_stats()

    def _cpu_stats(self):
        import psutil
        percents = psutil.cpu_percent(None, True)
        stats = {}
        if self._cpu_percent_init:
            i = 0
            for percent in percents:
                stats["sys/cpu%i/util" % i] = percent / 100
                i += 1
            if percents:
                stats["sys/cpu/util"] = sum(percents) / len(percents) / 100
        self._cpu_percent_init = True
        return stats
