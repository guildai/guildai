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

import hashlib
import logging
import os
import re

import guild.opref

from guild import pip_util
from guild import util
from guild import var

log = logging.getLogger("guild")

class ResolutionError(Exception):
    pass

class Resolver(object):

    def __init__(self, source, config):
        self.source = source
        self.config = config

    def resolve(self, _unpack_dir=None):
        raise NotImplementedError()

class FileResolver(Resolver):

    def __init__(self, source, config, working_dir=None):
        super(FileResolver, self).__init__(source, config)
        self.working_dir = working_dir or os.getcwd()

    def resolve(self, unpack_dir=None):
        if self.config:
            return _resolve_config_path(self)
        source_path = os.path.join(
            self.working_dir, self.source.parsed_uri.path)
        if os.path.isdir(source_path):
            return [source_path]
        else:
            return resolve_source_files(source_path, self.source, unpack_dir)

def _resolve_config_path(res):
    assert res.config
    config_path = os.path.abspath(res.config)
    if not os.path.exists(config_path):
        raise ResolutionError("%s does not exist" % config_path)
    log.info("Using %s for %s resource", config_path, res.source.resdef.name)
    return [config_path]

class URLResolver(Resolver):

    def resolve(self, unpack_dir=None):
        if self.config:
            return _resolve_config_path(self)
        download_dir = self._source_download_dir()
        util.ensure_dir(download_dir)
        try:
            source_path = pip_util.download_url(
                self.source.uri,
                download_dir,
                self.source.sha256)
        except pip_util.HashMismatch as e:
            raise ResolutionError(
                "bad sha256 for '%s' (expected %s but got %s)"
                % (self.source.uri, e.expected, e.actual))
        else:
            return resolve_source_files(source_path, self.source, unpack_dir)

    def _source_download_dir(self):
        key = "\n".join(self.source.parsed_uri).encode("utf-8")
        digest = hashlib.sha224(key).hexdigest()
        return os.path.join(var.cache_dir("resources"), digest)

class OperationOutputResolver(Resolver):

    def __init__(self, source, config, modeldef):
        super(OperationOutputResolver, self).__init__(source, config)
        self.modeldef = modeldef

    def resolve(self, unpack_dir=None):
        config_run_spec = self.config
        source_path = self._source_path_for_run_spec(config_run_spec)
        return resolve_source_files(source_path, self.source, unpack_dir)

    def _source_path_for_run_spec(self, run_spec):
        if run_spec and os.path.isdir(run_spec):
            log.info(
                "Using output in %s for %s resource",
                run_spec, self.source.resdef.name)
            return run_spec
        else:
            run = self._latest_op_run(run_spec)
            log.info(
                "Using output from run %s for %s resource",
                run.id, self.source.resdef.name)
            return run.path

    def _latest_op_run(self, run_id_prefix):
        oprefs = self._source_oprefs()
        runs_filter = self._runs_filter(oprefs, run_id_prefix)
        runs = var.runs(sort=["-started"], filter=runs_filter)
        if runs:
            return runs[0]
        raise ResolutionError(
            "no suitable run for %s"
            % ",".join([self._opref_desc(opref) for opref in oprefs]))

    def _source_oprefs(self):
        oprefs = []
        for spec in self._split_opref_specs(self.source.parsed_uri.path):
            try:
                oprefs.append(guild.opref.OpRef.from_string(spec))
            except guild.opref.OpRefError:
                raise ResolutionError("inavlid operation reference %r" % spec)
        return oprefs

    @staticmethod
    def _split_opref_specs(spec):
        return [part.strip() for part in spec.split(",")]

    def _runs_filter(self, oprefs, run_id_prefix):
        if run_id_prefix:
            return lambda run: run.id.startswith(run_id_prefix)
        resolved_oprefs = [self._resolve_opref(opref) for opref in oprefs]
        return var.run_filter(
            "all", [
                var.run_filter("any", [
                    var.run_filter("attr", "status", "completed"),
                    var.run_filter("attr", "status", "running"),
                    var.run_filter("attr", "status", "terminated"),
                ]),
                var.run_filter("any", [
                    opref.is_op_run for opref in resolved_oprefs
                ])
            ])

    def _resolve_opref(self, opref):
        assert opref.op_name, opref
        return guild.opref.OpRef(
            pkg_type="package" if opref.pkg_name else None,
            pkg_name=opref.pkg_name,
            pkg_version=None,
            model_name=opref.model_name or self.modeldef.name,
            op_name=opref.op_name)

    @staticmethod
    def _opref_desc(opref):
        if opref.pkg_type == "guildfile":
            pkg = "./"
        elif opref.pkg_name:
            pkg = opref.pkg_name + "/"
        else:
            pkg = ""
        model_spec = pkg + (opref.model_name or "")
        return (
            "{}:{}".format(model_spec, opref.op_name)
            if model_spec else opref.op_name)

def resolve_source_files(source_path, source, unpack_dir):
    _verify_path(source_path, source.sha256)
    return _resolve_source_files(source_path, source, unpack_dir)

def _verify_path(path, sha256):
    if not os.path.exists(path):
        raise ResolutionError("'%s' does not exist" % path)
    if sha256:
        if os.path.isdir(path):
            log.warning("cannot verify '%s' because it's a directory", path)
            return
        _verify_file_hash(path, sha256)

def _verify_file_hash(path, sha256):
    actual = util.file_sha256(path, use_cache=True)
    if actual != sha256:
        raise ResolutionError(
            "'%s' has an unexpected sha256 (expected %s but got %s)"
            % (path, sha256, actual))

def _resolve_source_files(source_path, source, unpack_dir):
    if os.path.isdir(source_path):
        return _dir_source_files(source_path, source)
    else:
        unpacked = _maybe_unpack(source_path, source, unpack_dir)
        if unpacked is not None:
            return unpacked
        else:
            return [source_path]

def _dir_source_files(dir, source):
    if source.select:
        return _selected_source_paths(
            dir, _all_dir_files(dir), source.select)
    else:
        return _all_source_paths(dir, os.listdir(dir))

def _all_dir_files(dir):
    all = []
    for root, dirs, files in os.walk(dir):
        root = os.path.relpath(root, dir) if dir != root else ""
        for name in dirs + files:
            path = os.path.join(root, name)
            normalized_path = path.replace(os.path.sep, "/")
            all.append(normalized_path)
    return all

def _selected_source_paths(root, files, select):
    selected = set()
    patterns = [re.compile(s + "$") for s in select]
    for path in files:
        path = util.strip_trailing_path(path)
        for p in patterns:
            if p.match(path):
                selected.add(os.path.join(root, path))
    return list(selected)

def _all_source_paths(root, files):
    root_names = [path.split("/")[0] for path in files]
    return [
        os.path.join(root, name) for name in set(root_names)
        if not name.startswith(".guild")
    ]

def _maybe_unpack(source_path, source, unpack_dir):
    if not source.unpack:
        return None
    archive_type = _archive_type(source_path, source)
    if not archive_type:
        return None
    return _unpack(source_path, archive_type, source.select, unpack_dir)

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

def _unpack(source_path, archive_type, select, unpack_dir):
    unpack_dir = unpack_dir or os.path.dirname(source_path)
    unpacked = _list_unpacked(source_path, unpack_dir)
    if unpacked:
        return _from_unpacked(unpack_dir, unpacked, select)
    elif archive_type == "zip":
        return _unzip(source_path, select, unpack_dir)
    elif archive_type == "tar":
        return _untar(source_path, select, unpack_dir)
    else:
        raise ResolutionError(
            "'%s' cannot be unpacked "
            "(unsupported archive type '%s')"
            % (source_path, type))

def _list_unpacked(src, unpack_dir):
    unpacked_src = _unpacked_src(unpack_dir, src)
    unpacked_time = util.getmtime(unpacked_src)
    if not unpacked_time or unpacked_time < util.getmtime(src):
        return None
    lines = open(unpacked_src, "r").readlines()
    return [l.rstrip() for l in lines]

def _unpacked_src(unpack_dir, src):
    name = os.path.basename(src)
    return os.path.join(unpack_dir, ".guild-cache-%s.unpacked" % name)

def _from_unpacked(root, unpacked, select):
    if select:
        return _selected_source_paths(root, unpacked, select)
    else:
        return _all_source_paths(root, unpacked)

def _unzip(src, select, unpack_dir):
    import zipfile
    zf = zipfile.ZipFile(src)
    log.info("Unpacking %s", src)
    return _gen_unpack(
        unpack_dir,
        src,
        zf.namelist,
        lambda name: name,
        zf.extractall,
        select)

def _untar(src, select, unpack_dir):
    import tarfile
    tf = tarfile.open(src)
    log.info("Unpacking %s", src)
    return _gen_unpack(
        unpack_dir,
        src,
        tf.getmembers,
        lambda tfinfo: tfinfo.name,
        tf.extractall,
        select)

def _gen_unpack(unpack_dir, src, list_members, member_name, extract_all, select):
    members = list_members()
    member_names = [member_name(m) for m in members]
    to_extract = [
        m for m in members
        if not os.path.exists(os.path.join(unpack_dir, member_name(m)))]
    extract_all(unpack_dir, to_extract)
    _write_unpacked(member_names, unpack_dir, src)
    if select:
        return _selected_source_paths(unpack_dir, member_names, select)
    else:
        return _all_source_paths(unpack_dir, member_names)

def _write_unpacked(unpacked, unpack_dir, src):
    with open(_unpacked_src(unpack_dir, src), "w") as f:
        for path in unpacked:
            f.write(path + "\n")
