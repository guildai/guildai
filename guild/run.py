import os

import guild.util

class Run(object):

    def __init__(self, id, path):
        self.id = id
        self.path = path
        self._guild_dir = os.path.join(self.path, ".guild")

    @property
    def short_id(self):
        return self.id[:8]

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

    def guild_path(self, subpath):
        return os.path.join(self._guild_dir, subpath)

def _parse_attr(raw):
    return raw.strip()
