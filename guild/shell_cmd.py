import os
import subprocess
import sys

def main(_args):
    env = {
        "PYTHONPATH": os.path.pathsep.join(sys.path)
    }
    p = subprocess.Popen([sys.executable, "-Ss"], env=env)
    p.communicate()
