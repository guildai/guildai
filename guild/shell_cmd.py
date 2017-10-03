import os
import subprocess
import sys

def main(_args):
    env = {
        "PYTHONPATH": os.path.pathsep.join(sys.path),
        "LD_LIBRARY_PATH": os.getenv("LD_LIBRARY_PATH"),
    }
    p = subprocess.Popen(
        [sys.executable, "-Ssic", "import guild.app;guild.app.init()"],
        env=env)
    p.communicate()
