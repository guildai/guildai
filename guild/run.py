import os

import guild.util

class Run(object):

    __properties__ = [
        "id",
        "path",
        "short_id",
        "status",
        "extended_status"
    ]

    def __init__(self, id, path):
        self.id = id
        self.path = path
        self._guild_dir = os.path.join(self.path, ".guild")
        self._status = None
        self._extended_status = None

    @property
    def short_id(self):
        return self.id[:8]

    @property
    def status(self):
        if self._status is None:
            self._status = _op_status(self)
        return self._status

    @property
    def extended_status(self):
        if self._extended_status is None:
            self._extended_status = _extended_op_status(self)
        return self._extended_status

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def __getitem__(self, name):
        attr_path = os.path.join(self._guild_dir, "attrs", name)
        try:
            raw = open(attr_path, "r").read()
        except IOError:
            raise KeyError(name)
        else:
            return _parse_attr(raw)

    def __repr__(self):
        return "<guild.run.Run '%s'>" % self.id

    def init_skel(self):
        guild.util.ensure_dir(self.guild_path("attrs"))
        guild.util.ensure_dir(self.guild_path("logs"))

    def update_status(self):
        self._status = None
        self._extended_status = None

    def guild_path(self, subpath):
        return os.path.join(self._guild_dir, subpath)

def _parse_attr(raw):
    return raw.strip()

def _op_status(run):
    pid = _op_pid(run)
    if pid is None:
        return "stopped"
    elif guild.util.pid_exists(pid):
        return "running"
    else:
        return "crashed"

def _op_pid(run):
    lockfile = run.guild_path("LOCK")
    try:
        raw = open(lockfile, "r").read()
    except (IOError, ValueError):
        return None
    else:
        return int(raw)

def _extended_op_status(run):
    """Uses exit_status to extend the status to include error or success."""
    base_status = run.status
    if base_status == "running":
        return "running"
    elif base_status == "crashed":
        return "terminated"
    elif base_status == "stopped":
        if run.get("exit_status") == "0":
            return "completed"
        else:
            return "error"
    else:
        raise AssertionError(base_status)
