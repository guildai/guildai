import subprocess
import sys

import guild.plugin

class GPUPlugin(guild.plugin.Plugin):

    def init(self):
        self._smi = _smi_cmd()

    def enabled_for_op(self, _op):
        return self._smi is not None

    def patch_env(self):
        import tensorflow
        guild.plugin.listen_method(
            tensorflow.summary.FileWriter.add_summary,
            self._summary)

    def _summary(add_summary, *args, **kw):
        print("********** ", args, kw)

def _smi_cmd():
    try:
        out = subprocess.check_output(["which", "nvidia-smi"])
    except OSError:
        return None
    else:
        return out.strip()
