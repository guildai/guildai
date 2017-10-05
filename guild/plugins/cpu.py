from __future__ import division

from guild.plugins.tensorflow import SummaryPlugin

class CPUPlugin(SummaryPlugin):

    SUMMARY_NAME = "cpu stats"

    def __init__(self):
        super(CPUPlugin, self).__init__()
        self._cpu_percent_init = False

    def enabled_for_op(self, _op):
        return True

    def read_summary_values(self):
        return self._cpu_stats()

    def _cpu_stats(self):
        import psutil
        percents = psutil.cpu_percent(None, True)
        stats = {}
        if self._cpu_percent_init:
            i = 0
            for percent in percents:
                stats["system/cpu%i/util" % i] = percent / 100
                i += 1
            if percents:
                stats["system/cpu/util"] = sum(percents) / len(percents) / 100
        self._cpu_percent_init = True
        return stats
