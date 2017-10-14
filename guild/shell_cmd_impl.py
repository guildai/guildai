import os
import subprocess
import sys

import guild.util

def main(_args):
    env = guild.util.safe_osenv()
    env["PYTHONPATH"] = os.path.pathsep.join(sys.path)
    p = subprocess.Popen([sys.executable, "-Ssi"], env=env)
    p.communicate()
