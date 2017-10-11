import os
import subprocess

import guild

def version():
    _maybe_init_git_commit()
    if guild.__git_commit__:
        return "%s (git commit %s)" % (guild.__version__, guild.__git_commit__)
    else:
        return guild.__version__

def _maybe_init_git_commit():
    if not hasattr(guild, "__git_commit__"):
        guild.__git_commit__ = _git_commit()

def _git_commit():
    src_home = _find_source_home()
    if src_home:
        cmd = ("git -C \"%s\" log -1 --oneline | cut -d' ' -f1" % src_home)
        raw = subprocess.check_output(cmd, shell=True)
        return raw.strip()
    else:
        return None

def _find_source_home():
    cur = home()
    while True:
        if cur == "/" or cur == "":
            break
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        cur = os.path.dirname(cur)
    return None

def home():
    abs_file = os.path.abspath(__file__)
    return os.path.dirname(abs_file)

def script(name):
    return os.path.join(home(), "scripts", name)
