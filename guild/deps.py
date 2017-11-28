# Copyright 2017 TensorHub, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division

import logging
import os
import re
import subprocess

from guild import namespace
from guild import resource
from guild import util
from guild.resolver import ResolutionError

log = logging.getLogger("guild")

RESOURCE_TERM = r"[a-zA-Z0-9_\-\.]+"

class DependencyError(Exception):
    pass

class ResolutionContext(object):

    def __init__(self, target_dir, opdef):
        self.target_dir = target_dir
        self.opdef = opdef

class Resource(object):

    def __init__(self, resdef, ctx):
        self.resdef = resdef
        self.ctx = ctx

    def resolve(self):
        log.info("Resolving %s resource", self.resdef.name)
        if not self.resdef.sources:
            log.warning(
                "%s resource does not define any sources",
                self.resdef.name)
        for source in self.resdef.sources:
            self._resolve_source(source)
        self._post_resolve()

    def _resolve_source(self, source):
        resolver = self.resdef.get_source_resolver(source)
        if not resolver:
            raise DependencyError(
                "unsupported source '%s' in %s resource"
                % (source, self.resdef.name))
        try:
            source_path = resolver.resolve()
        except ResolutionError as e:
            raise DependencyError(
                "could not resolve '%s' in %s resource: %s"
                % (source, self.resdef.name, e))
        except Exception as e:
            if log.getEffectiveLevel() <= logging.DEBUG:
                log.exception("dependency resolve")
            raise DependencyError(
                "could not resolve '%s' in %s resource: %s"
                % (source, self.resdef.name, e))
        else:
            self._verify_path(source_path, source.sha256)
            log.info(
                "Using %s for %s resource",
                source_path, source.resdef.name)
            source_files = self._resolve_source_files(source_path, source)
            for path in source_files:
                self._link_to_source(path)

    def _verify_path(self, path, sha256):
        self._verify_file_exists(path)
        if sha256:
            if os.path.isdir(path):
                raise DependencyError(
                    "'%s' required by operation '%s' cannot be verified "
                    "using sha256 because it is a directory"
                    % (path, self.ctx.opdef.fullname))
            self._verify_file_hash(path, sha256)

    def _verify_file_exists(self, path):
        if not os.path.exists(path):
            raise DependencyError(
                "'%s' required by operation '%s' does not exist"
                % (path, self.ctx.opdef.fullname))

    def _verify_file_hash(self, path, sha256):
        actual = util.file_sha256(path)
        if actual != sha256:
            raise DependencyError(
                "'%s' required by operation '%s' has an unexpected sha256 "
                "(expected %s but got %s)"
                % (path, self.ctx.opdef.fullname, sha256, actual))

    def _resolve_source_files(self, source_path, source):
        if os.path.isdir(source_path):
            return self._dir_source_files(source_path, source)
        else:
            unpacked = self._maybe_unpack(source_path, source)
            if unpacked is None:
                return [source_path]
            else:
                return unpacked

    def _dir_source_files(self, dir, source):
        if source.select:
            return self._selected_source_paths(
                dir, self._all_dir_files(dir), source.select)
        else:
            return self._all_source_paths(dir, os.listdir(dir))

    @staticmethod
    def _all_dir_files(dir):
        all = []
        for root, dirs, files in os.walk(dir):
            root = os.path.relpath(root, dir) if dir != root else ""
            for name in dirs + files:
                path = os.path.join(root, name)
                normalized_path = path.replace(os.path.sep, "/")
                all.append(normalized_path)
        return all

    @staticmethod
    def _selected_source_paths(root, files, select):
        selected = set()
        pattern = re.compile(select + "$")
        for path in files:
            if path.startswith(".guild/"):
                continue
            path = util.strip_trailing_path(path)
            match = pattern.match(path)
            if not match:
                continue
            if match.groups():
                path = match.group(1)
            selected.add(os.path.join(root, path))
        return list(selected)

    @staticmethod
    def _all_source_paths(root, files):
        root_names = [path.split("/")[0] for path in files]
        return [
            os.path.join(root, name) for name in set(root_names)
            if name != ".guild"
        ]

    def _maybe_unpack(self, source_path, source):
        if not source.unpack:
            return None
        archive_type = self._archive_type(source_path, source)
        if not archive_type:
            return None
        return self._unpack(source_path, archive_type, source.select)

    @staticmethod
    def _archive_type(source_path, source):
        if source.type:
            return source.type
        parts = source_path.lower().split(".")
        if parts[-1] == "zip":
            return "zip"
        elif (parts[-1] == "tar" or
              parts[-1] == "tgz" or
              parts[-2:-1] == ["tar"]):
            return "tar"
        else:
            return None

    def _unpack(self, source_path, type, select):
        if type == "zip":
            return self._unzip(source_path, select)
        elif type == "tar":
            return self._untar(source_path, select)
        else:
            raise DependencyError(
                "'%s' required by operation '%s' cannot be unpacked "
                "(unsupported archive type '%s')"
                % (source_path, self.ctx.opdef.fullname, type))

    def _unzip(self, source_path, select):
        import zipfile
        zf = zipfile.ZipFile(source_path)
        return self._gen_unpack(
            os.path.dirname(source_path),
            zf.namelist,
            lambda name: name,
            zf.extractall,
            select)

    def _untar(self, source_path, select):
        import tarfile
        tf = tarfile.open(source_path)
        return self._gen_unpack(
            os.path.dirname(source_path),
            tf.getmembers,
            lambda tfinfo: tfinfo.name,
            tf.extractall,
            select)

    def _gen_unpack(self, root, list_members, member_name, extract_all, select):
        members = list_members()
        member_names = [member_name(m) for m in members]
        to_extract = [
            m for m in members
            if not os.path.exists(os.path.join(root, member_name(m)))]
        extract_all(root, to_extract)
        if select:
            return self._selected_source_paths(root, member_names, select)
        else:
            return self._all_source_paths(root, member_names)

    def _link_to_source(self, source_path):
        source_path = util.strip_trailing_path(source_path)
        link = self._link_path(source_path)
        if os.path.exists(link):
            log.warning("source '%s' already exists, skipping link", link)
            return
        util.ensure_dir(os.path.dirname(link))
        log.debug("resolving source '%s' as link '%s'", source_path, link)
        os.symlink(source_path, link)

    def _link_path(self, source_path):
        basename = os.path.basename(source_path)
        res_path = self.resdef.path or ""
        if os.path.isabs(res_path):
            raise DependencyError(
                "invalid path '%s' in %s resource (path must be relative)"
                % (res_path, self.resdef.name))
        return os.path.join(self.ctx.target_dir, res_path, basename)

    def _post_resolve(self):
        if not self.resdef.post_resolve:
            return
        log.info(
            "Performing post resolve actions for %s resource",
            self.resdef.name)
        log.debug("post resolve: %s", self.resdef.post_resolve)
        try:
            subprocess.check_call(
                self.resdef.post_resolve,
                shell=True,
                cwd=self.ctx.target_dir)
        except subprocess.CalledProcessError as e:
            raise DependencyError(
                "error generated by post-resolve in %s resource: %s"
                % (self.resdef.name, e))

def _dep_desc(dep):
    return "%s:%s" % (dep.opdef.modeldef.name, dep.opdef.name)

def resolve(dependencies, ctx):
    for dep in dependencies:
        resource = _dependency_resource(dep.spec, ctx)
        resource.resolve()

def _dependency_resource(spec, ctx):
    resolved_spec = util.resolve_refs(spec, ctx.opdef.flag_values())
    res = util.find_apply(
        [_model_resource,
         _modelfile_resource,
         _packaged_resource],
        resolved_spec, ctx)
    if res:
        return res
    raise DependencyError(
        "invalid dependency '%s' in operation '%s'"
        % (resolved_spec, ctx.opdef.fullname))

def _model_resource(spec, ctx):
    m = re.match(r"(%s)$" % RESOURCE_TERM, spec)
    if m is None:
        return None
    res_name = m.group(1)
    return _modeldef_resource(ctx.opdef.modeldef, res_name, ctx)

def _modeldef_resource(modeldef, res_name, ctx):
    resdef = modeldef.get_resource(res_name)
    if resdef is None:
        raise DependencyError(
            "resource '%s' required by operation '%s' is not defined"
            % (res_name, ctx.opdef.fullname))
    return Resource(resdef, ctx)

def _modelfile_resource(spec, ctx):
    m = re.match(r"(%s):(%s)$" % (RESOURCE_TERM, RESOURCE_TERM), spec)
    if m is None:
        return None
    model_name = m.group(1)
    modeldef = ctx.opdef.modelfile.get(model_name)
    if modeldef is None:
        raise DependencyError(
            "model in resource '%s' required by operation "
            "'%s' is not defined"
            % (spec, ctx.opdef.fullname))
    res_name = m.group(2)
    return _modeldef_resource(modeldef, res_name, ctx)

def _packaged_resource(spec, ctx):
    m = re.match(r"(%s)/(%s)$" % (RESOURCE_TERM, RESOURCE_TERM), spec)
    if m is None:
        return None
    pkg_name = m.group(1)
    res_name = m.group(2)
    try:
        resources = list(resource.for_name(res_name))
    except LookupError:
        pass
    else:
        for res in resources:
            if namespace.apply_namespace(res.dist.project_name) == pkg_name:
                return Resource(res.resdef, ctx)
    raise DependencyError(
        "resource '%s' required by operation '%s' is not installed"
        % (spec, ctx.opdef.fullname))
