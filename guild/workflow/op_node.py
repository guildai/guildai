# Copyright 2017-2018 TensorHub, Inc.
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

from guild import deps as depslib
from guild import workflow as wf

from guild.workflow import file_node

class OpNode(wf.Node):

    def __init__(self, op, quiet=False):
        self.op = op
        self.quiet = quiet

    def get_description(self):
        return "Operation '{}'".format(self.op.opdef.fullname)

    def get_deps(self):
        deps = []
        ctx = depslib.ResolutionContext(
            target_dir=self.op.run_dir,
            opdef=self.op.opdef,
            resource_config=self.op.resource_config)
        resources = depslib.resources(self.op.opdef.dependencies, ctx)
        for res in resources:
            for source in res.resdef.sources:
                deps.append(_node_for_source(source, res))
        return deps

    def run(self):
        exit_status = self.op.run(self.quiet, skip_deps=True)
        if exit_status != 0:
            raise wf.RunError("non-zero exit for run in %s" % self.op.run_dir)

def _node_for_source(source, resource):
    uri_scheme = source.parsed_uri.scheme
    if uri_scheme == "file":
        return file_node.FileNode(source, resource)
    else:
        raise AssertionError(source)
