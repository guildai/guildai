import logging
import os

class UnresolvedResource(object):

    def __init__(self, ep, init):
        self._ep = ep
        self._init = init

    def resolve(self):
        res = self._ep.resolve()()
        if self._init:
            self._init(res, self._ep)
        return res

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
        return {
            ep.name: UnresolvedResource(ep, self._init)
            for ep in working_set.iter_entry_points(self._group)
        }

    def __iter__(self):
        for name in self._resources:
            yield name, self.for_name(name)

    def for_name(self, name):
        try:
            res = self._resources[name]
        except KeyError:
            raise LookupError(name)
        else:
            if isinstance(res, UnresolvedResource):
                logging.debug("initializing %s '%s' (%s)", self._desc, name, res)
                self._resources[name] = res = res.resolve()
        return res

    def limit_to_builtin(self):
        import guild
        import pkg_resources
        guild_pkg_path = os.path.dirname(guild.__path__[0])
        self._working_set = pkg_resources.WorkingSet([guild_pkg_path])
