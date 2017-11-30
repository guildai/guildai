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

import guild.opref

from guild import pip_util
from guild import util
from guild import var

log = logging.getLogger("guild")

class ResolutionError(Exception):
    pass

class Resolver(object):

    def resolve(self, _config):
        raise NotImplementedError()

class FileResolver(Resolver):

    def __init__(self, source, working_dir=None):
        working_dir = working_dir or os.getcwd()
        self.source = source
        self.working_dir = working_dir

    def resolve(self, config):
        if config:
            log.warning("ignoring config %r for file resource", config)
        source_path = os.path.join(
            self.working_dir, self.source.parsed_uri.path)
        if not os.path.exists(source_path):
            raise ResolutionError("file '%s' does not exist" % source_path)
        return source_path

class URLResolver(Resolver):

    def __init__(self, source):
        self.source = source

    def resolve(self, config):
        if config:
            log.warning("ignoring config %r for URL resource", config)
        download_dir = self._source_download_dir()
        util.ensure_dir(download_dir)
        try:
            return pip_util.download_url(
                self.source.uri,
                download_dir,
                self.source.sha256)
        except pip_util.HashMismatch as e:
            raise ResolutionError(
                "bad sha256 for '%s' (expected %s but got %s)"
                % (self.source.uri, e.expected, e.actual))

    def _source_download_dir(self):
        key = "\n".join(self.source.parsed_uri).encode("utf-8")
        digest = hashlib.sha224(key).hexdigest()
        return os.path.join(var.cache_dir("resources"), digest)

class OperationOutputResolver(Resolver):

    def __init__(self, source, modeldef):
        self.source = source
        self.modeldef = modeldef

    def resolve(self, run_spec):
        oprefs = self._source_oprefs()
        if run_spec and os.path.isdir(run_spec):
            return run_spec
        else:
            run = self._latest_op_run(oprefs, run_spec)
            return run.path

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

    def _latest_op_run(self, oprefs, run_id_prefix):
        runs_filter = self._runs_filter(oprefs, run_id_prefix)
        runs = var.runs(sort=["-started"], filter=runs_filter)
        if runs:
            return runs[0]
        raise ResolutionError(
            "no suitable run for %s"
            % ",".join([self._opref_desc(opref) for opref in oprefs]))

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
        if opref.pkg_type == "modelfile":
            pkg = "./"
        elif opref.pkg_name:
            pkg = opref.pkg_name + "/"
        else:
            pkg = ""
        return "%s%s:%s" % (pkg, opref.model_name, opref.op_name)
