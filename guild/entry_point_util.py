import logging
import os

class Resource(object):

    def __init__(self, ep, init):
        self._ep = ep
        self._init = init
        self._inst = None

    def inst(self):
        if self._inst is None:
            self._inst = self._ep.resolve()()
            if self._init:
                self._init(self._inst, self._ep)
        return self._inst

    def __str__(self):
        parts = [self._ep.module_name]
        if self._ep.attrs:
            parts.extend([":", ".".join(self._ep.attrs)])
        if self._ep.extras:
            parts.extend([" [", ','.join(self._ep.extras), "]"])
        return "".join(parts)

class EntryPointResources(object):

    def __init__(self, group, resource_desc="resource", resource_init=None):
        self._group = group
        self._desc = resource_desc
        self._init = resource_init
        self._working_set = None
        self.__resources = None

    @property
    def _resources(self):
        if self.__resources is None:
            self.__resources = self._init_resources()
        return self.__resources

    def _init_resources(self):
        import pkg_resources
        working_set = self._working_set or pkg_resources.working_set
        resources = {}
        for ep in working_set.iter_entry_points(self._group):
            res_list = resources.setdefault(ep.name, [])
            res_list.append(Resource(ep, self._init))
        return resources

    def __iter__(self):
        for name in self._resources:
            for res_inst in self.for_name(name):
                yield name, res_inst

    def one_for_name(self, name):
        return self.for_name(name)[0]

    def for_name(self, name):
        try:
            name_resources = self._resources[name]
        except KeyError:
            raise LookupError(name)
        else:
            return [res.inst() for res in name_resources]

    def limit_to_builtin(self):
        import guild
        import pkg_resources
        guild_pkg_path = os.path.dirname(guild.__path__[0])
        self._working_set = pkg_resources.WorkingSet([guild_pkg_path])

    def limit_to_paths(self, paths):
        import pkg_resources
        self._working_set = pkg_resources.WorkingSet(paths)
