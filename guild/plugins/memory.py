# Copyright 2017-2020 TensorHub, Inc.
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

from guild.plugins.summary_util import SummaryPlugin


class MemoryPlugin(SummaryPlugin):
    def enabled_for_op(self, _op):
        try:
            import psutil as _
        except ImportError as e:
            self.log.warning(
                "memory stats disabled because psutil " "cannot be imported (%s)", e
            )
            return False, "error importing psutil: %s" % e
        else:
            return True, ""

    def read_summary_values(self, _step):
        return _mem_stats()


def _mem_stats():
    import psutil

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "sys/mem_total": mem.total,
        "sys/mem_free": mem.free,
        "sys/mem_used": mem.used,
        "sys/mem_util": mem.percent / 100,
        "sys/swap_total": swap.total,
        "sys/swap_free": swap.free,
        "sys/swap_used": swap.used,
        "sys/swap_util": swap.percent / 100,
    }
