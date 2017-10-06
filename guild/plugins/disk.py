from __future__ import division

import time

from guild.plugins.tensorflow_util import SummaryPlugin

class DiskPlugin(SummaryPlugin):

    SUMMARY_NAME = "disk stats"

    def __init__(self):
        super(DiskPlugin, self).__init__()
        self._last_disk = None

    def enabled_for_op(self, _op):
        return True

    def read_summary_values(self):
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
        full_name = device.device
        if not full_name.startswith('/dev/'):
            raise AssertionError(full_name)
        name = full_name[5:]
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
    return "system/dev%s/%s" % (dev_name, stat_name)
