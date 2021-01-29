import os

import psutil

this_p = psutil.Process(os.getpid())
parent_p = psutil.Process(os.getppid())

parent_cmd = parent_p.cmdline()
assert (
    len(parent_cmd) > 4
    and parent_cmd[1].endswith("guild")
    and parent_cmd[2] == "run"
    and ("kill" in parent_cmd[2:] or "kill.py" in parent_cmd[2:])
), parent_cmd

parent_p.kill()
this_p.kill()
