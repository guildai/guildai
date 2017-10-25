import logging
import os

from guild import util

class ResolutionContext(object):

    def __init__(self, target_dir, source_dir):
        self.target_dir = target_dir
        self.source_dir = source_dir

class LocalFileResolver(object):

    def __init__(self, dep, ctx):
        self.dep = dep
        self.ctx = ctx

    def __str__(self):
        return "local file dependency '%s'" % self.dep

    def resolve(self):
        source_path = os.path.join(self.ctx.source_dir, self.dep)
        target_path = os.path.join(self.ctx.target_dir, self.dep)
        util.ensure_dir(os.path.dirname(target_path))
        logging.debug("linking %s to %s", source_path, target_path)
        os.symlink(source_path, target_path)

def resolve(deps, ctx):
    for dep in deps:
        resolver = _resolver_for_dep(dep, ctx)
        logging.debug("resolving %s", resolver)
        resolver.resolve()

def _resolver_for_dep(dep, ctx):
    # The only type we support atm
    return LocalFileResolver(dep, ctx)
