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

import time

from guild.plugins.tensorflow_util import SummaryPlugin

class PerfPlugin(SummaryPlugin):

    def __init__(self, ep):
        super(PerfPlugin, self).__init__(ep)
        self._last_step = None
        self._last_time = None

    def enabled_for_op(self, _op):
        return True, ""

    def read_summary_values(self, step):
        cur_time = time.time()
        stats = {}
        if self._last_step is not None:
            assert self._last_time is not None
            steps = step - self._last_step
            if steps > 0:
                seconds = cur_time - self._last_time
                stats["performance/sec_per_step"] = seconds / steps
                stats["performance/step_per_sec"] = steps / seconds
        self._last_step = step
        self._last_time = cur_time
        return stats
