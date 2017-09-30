import os

import guild.util

class Run(object):

    __properties__ = [
        "id",
        "path",
        "short_id",
        "pid",
        "status",
        "extended_status"
    ]

    def __init__(self, id, path):
        self.id = id
        self.path = path
        self._guild_dir = os.path.join(self.path, ".guild")
        self._pid = None
        self._status = None
        self._extended_status = None

    @property
    def short_id(self):
        return self.id[:8]

    @property
    def pid(self):
        if self._pid is None:
            self._pid = _op_pid(self)
        return self._pid

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
        try:
            raw = open(self._attr_path(name), "r").read()
        except IOError:
            raise KeyError(name)
        else:
            return _parse_attr(raw)

    def _attr_path(self, name):
        return os.path.join(self._guild_dir, "attrs", name)

    def __repr__(self):
        return "<guild.run.Run '%s'>" % self.id

    def init_skel(self):
        guild.util.ensure_dir(self.guild_path("attrs"))
        guild.util.ensure_dir(self.guild_path("logs"))

    def update_status(self):
        """Update status and extended_status.

        The attribute status and extended_status are expensive to read
        (OS side effects) and so are read lazily and cached. Use this
        method to update these attributes to the latest value.

        (Note that calling this method merely invalidates the cached
        values - new values are read lazily.)
        """
        self._pid = None
        self._status = None
        self._extended_status = None

    def guild_path(self, subpath):
        return os.path.join(self._guild_dir, subpath)

    def write_attr(self, name, val):
        with open(self._attr_path(name), "w") as f:
            f.write(_encode_attr(val))

def _parse_attr(raw):
    return raw.strip()

def _encode_attr(val):
    if isinstance(val, list):
        return "\n".join([str(x) for x in val])
    elif isinstance(val, dict):
        return "\n".join([
            "%s: %s" % (str(item_key), str(item_val))
            for item_key, item_val in val.items()
        ])
    else:
        return str(val)

def _op_pid(run):
    lockfile = run.guild_path("LOCK")
    try:
        raw = open(lockfile, "r").read()
    except (IOError, ValueError):
        return None
    else:
        return int(raw)

def _op_status(run):
    pid = run.pid
    if pid is None:
        return "stopped"
    elif guild.util.pid_exists(pid):
        return "running"
    else:
        return "crashed"

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
