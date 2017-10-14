import os
import subprocess

__version__ = "0.1.0-2"

def _try_init_git_attrs():
    try:
        _init_git_commit()
    except (OSError, subprocess.CalledProcessError):
        pass
    else:
        try:
            _init_git_status()
        except (OSError, subprocess.CalledProcessError):
            pass

def _init_git_commit():
    commit = _git_cmd("git -C \"%(repo)s\" log -1 --oneline | cut -d' ' -f1")
    globals()["__git_commit__"] = commit

def _init_git_status():
    raw = _git_cmd("git -C \"%(repo)s\" status -s")
    globals()["__git_status__"] = raw.split("\n") if raw else []

def _git_cmd(cmd, **kw):
    repo = os.path.dirname(__file__)
    cmd = cmd % dict(repo=repo, **kw)
    return subprocess.check_output(cmd, shell=True).strip()

def version():
    git_commit = globals().get("__git_commit__")
    if git_commit:
        git_status = globals().get("__git_status__", [])
        workspace_changed_marker = "*" if git_status else ""
        return "%s (dev %s%s)" % (__version__, git_commit,
                                 workspace_changed_marker)
    else:
        return __version__

_try_init_git_attrs()
