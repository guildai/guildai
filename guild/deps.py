import hashlib
import logging
import os

from guild import util

class ResolutionContext(object):

    def __init__(self, target_dir, source_dir):
        self.target_dir = target_dir
        self.source_dir = source_dir

class DependencyError(Exception):

    def __init__(self, msg, dep):
        self.msg = msg
        self.dep = dep

    def __str__(self):
        return "%s (required by operation %s as '%s')" % (
            self.msg, self.dep.opdef.fullname, self.dep.spec)

def _dep_desc(dep):
    return "%s:%s" % (dep.opdef.modeldef.name, dep.opdef.name)

def resolve(deps, ctx):
    for dep in deps:
        for source in dep.iter_sources():
            url = util.parse_url(source.url)
            if url.scheme == "file":
                return _resolve_file(url.path, source, dep, ctx)
            else:
                raise DependencyError(
                    "unsupported URL scheme '%s' in '%s'"
                    % (url.scheme, source.url), dep)

def _resolve_file(path, source, dep, ctx):
    source_path = os.path.join(ctx.source_dir, path)
    _validate_file(source_path, source, dep)
    target_path = os.path.join(ctx.target_dir, os.path.basename(path))
    util.ensure_dir(os.path.dirname(target_path))
    logging.debug("linking %s to %s", source_path, target_path)
    os.symlink(source_path, target_path)

def _validate_file(path, source, dep):
    logging.debug("validating file '%s'", path)
    _validate_file_exists(path, dep)
    if source.sha256:
        _validate_file_sha256(path, source.sha256, dep)

def _validate_file_exists(path, dep):
    if not os.path.isfile(path):
        raise DependencyError("'%s' does not exist" % path, dep)

def _validate_file_sha256(path, expected, dep):
    actual = util.file_sha256(path)
    logging.debug("file '%s' has sha256 '%s'", path, actual)
    if actual != expected:
        raise DependencyError(
            "sha256 for '%s' is '%s', expected '%s'"
            % (path, actual, expected), dep)
