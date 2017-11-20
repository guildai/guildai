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
import os

import guild.opref

from guild import pip_util
from guild import util
from guild import var

class ResolutionError(Exception):
    pass

class Resolver(object):

    def resolve(self):
        raise NotImplementedError()

class FileResolver(Resolver):

    def __init__(self, source, working_dir=None):
        working_dir = working_dir or os.getcwd()
        self.source = source
        self.working_dir = working_dir

    def resolve(self):
        source_path = os.path.join(
            self.working_dir, self.source.parsed_uri.path)
        if not os.path.exists(source_path):
            raise ResolutionError("file '%s' does not exist" % source_path)
        return source_path

class URLResolver(Resolver):

    def __init__(self, source):
        self.source = source

    def resolve(self):
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

    def resolve(self):
        opref, path = self._source_opref()
        run = self._latest_op_run(opref)
        source_path = os.path.join(run.path, path)
        if not os.path.exists(source_path):
            raise ResolutionError(
                "required output '%s' was not generated in the latest run (%s)"
                % (path, run.id))
        return source_path

    def _source_opref(self):
        spec = self.source.parsed_uri.path
        try:
            opref, path = guild.opref.OpRef.from_string(spec)
        except guild.opref.OpRefError:
            raise ResolutionError(
                "inavlid operation reference '%s'" % spec)
        else:
            self._validate_path(path)
            normalized_path = os.path.join(*path[2:].split("/"))
            if not normalized_path:
                raise ResolutionError(
                    "invalid operation source path '%s' "
                    "(paths may not be empty)" % path)
            return opref, normalized_path

    @staticmethod
    def _validate_path(path):
        if not path:
            raise ResolutionError(
                "missing output path (operation must be in "
                "the format OP_NAME//PATH)")
        elif path[:2] != "//":
            raise ResolutionError(
                "invalid operation source path '%s' "
                "(paths must start with '//')" % path)

    def _latest_op_run(self, opref):
        resolved_opref = self._fully_resolve_opref(opref)
        completed_op_runs = var.run_filter("all", [
            var.run_filter("any", [
                var.run_filter("attr", "status", "completed"),
                var.run_filter("attr", "status", "running"),
            ]),
            resolved_opref.is_op_run])
        runs = var.runs(sort=["-started"], filter=completed_op_runs)
        if runs:
            return runs[0]
        raise ResolutionError(
            "no suitable run for %s" % self._opref_desc(resolved_opref))

    @staticmethod
    def _opref_desc(opref):
        pkg = "." if opref.pkg_type == "modelfile"  else opref.pkg_name
        return "%s/%s:%s" % (pkg, opref.model_name, opref.op_name)

    def _fully_resolve_opref(self, opref):
        assert opref.op_name, opref
        pkg_type = (
            opref.pkg_type or
            "package" if opref.pkg_name else "modelfile")
        pkg_name = (
            opref.pkg_name or
            os.path.abspath(self.modeldef.modelfile.dir))
        model_name = opref.model_name or self.modeldef.name
        op_name = opref.op_name
        return guild.opref.OpRef(
            pkg_type=pkg_type,
            pkg_name=pkg_name,
            pkg_version=None,
            model_name=model_name,
            op_name=op_name)
