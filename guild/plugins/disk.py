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

import platform
import re
import sys
import time

from guild.plugins.tensorflow_util import SummaryPlugin

PLATFORM = platform.system()

class DiskPlugin(SummaryPlugin):

    def __init__(self, ep):
        super(DiskPlugin, self).__init__(ep)
        self._last_disk = None

    def enabled_for_op(self, _op):
        if sys.platform == "darwin":
            return False, "disk stats not supported on darwin platform (Mac)"
        return True, ""

    def read_summary_values(self, _step):
        return self._disk_stats()

    def _disk_stats(self):
        stats = {}
        cur_disk = _timed_disk_io_counters()
        if self._last_disk:
            for dev_name, last, cur in _zip_physical_disk_stats(
                    self._last_disk, cur_disk):
                for stat_name, val in _calc_disk_stats(last, cur).items():
                    stats[_dev_stat_key(dev_name, stat_name)] = val
        self._last_disk = cur_disk
        return stats

def _timed_disk_io_counters():
    import psutil
    counters = {}
    now = time.time()
    for key, counts in psutil.disk_io_counters(True).items():
        counts_dict = counts._asdict()
        counts_dict["timestamp"] = now
        counters[key] = counts_dict
    return counters

def _zip_physical_disk_stats(all_last, all_cur):
    import psutil
    for device in psutil.disk_partitions():
        fullname = device.device
        if PLATFORM == "Windows":
            assert re.match(r"[A-Z]:\\$", fullname), fullname
            name = fullname[0]
        else:
            assert fullname.startswith('/dev/'), fullname
            name = fullname[5:]
        dev_last = all_last.get(name)
        dev_cur = all_cur.get(name)
        if dev_last and dev_cur:
            yield name, dev_last, dev_cur

def _calc_disk_stats(last, cur):
    stats = {}
    seconds = cur["timestamp"] - last["timestamp"]
    writes = cur["write_count"] - last["write_count"]
    reads = cur["read_count"] - last["read_count"]
    bytes_written = cur["write_bytes"] - last["write_bytes"]
    bytes_read = cur["read_bytes"] - last["read_bytes"]
    stats["wps"] = writes / seconds
    stats["rps"] = reads / seconds
    stats["wkbps"] = bytes_written / 1024 / seconds
    stats["rkbps"] = bytes_read / 1024 / seconds
    try:
        busy_time_ms = cur["busy_time"] - last["busy_time"]
    except KeyError:
        pass
    else:
        stats["util"] = busy_time_ms / (seconds * 1000)
    return stats

def _dev_stat_key(dev_name, stat_name):
    return "sys/dev%s/%s" % (dev_name, stat_name)
