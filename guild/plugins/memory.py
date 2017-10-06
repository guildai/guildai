from __future__ import division

from guild.plugins.tensorflow_util import SummaryPlugin

class MemoryPlugin(SummaryPlugin):

    SUMMARY_NAME = "memory stats"

    def enabled_for_op(self, _op):
        return True

    def read_summary_values(self):
        return _mem_stats()

def _mem_stats():
    import psutil
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "system/mem_total": mem.total,
        "system/mem_free": mem.free,
        "system/mem_used": mem.used,
        "system/mem_util": mem.percent / 100,
        "system/swap_total": swap.total,
        "system/swap_free": swap.free,
        "system/swap_used": swap.used,
        "system/swap_util": swap.percent / 100
    }
