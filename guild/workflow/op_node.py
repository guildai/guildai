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

from guild import util
from guild import workflow as wf

from guild.workflow import deps as depslib
from guild.workflow import sources_node

class OpInitNode(wf.Node):

    user_detail_level = wf.LOW

    def __init__(self, op):
        self.op = op

    def get_description(self):
        return "Initialize '{}'".format(self.op.opdef.fullname)

    def run(self):
        self.op.init()

class OpNode(wf.Node):

    user_detail_level = wf.HIGH

    def __init__(self, op, quiet=False):
        self.op = op
        self.quiet = quiet
        self.init_node = OpInitNode(op)

    def get_description(self):
        return "Run '{}'".format(self.op.opdef.fullname)

    def deps(self):
        yield self.init_node
        for resdef in self._dep_resdefs():
            yield self._resource_node(resdef)

    def _dep_resdefs(self):
        for dep in self.op.opdef.dependencies:
            spec = util.resolve_refs(dep.spec, self.op.flag_vals)
            resdef = depslib.dep_resdef(dep.spec, self.op.opdef)
            if resdef is None:
                raise wf.DepError(
                    "cannot find resource '%s' required by operation '%s'"
                    % (spec, self.op.opdef.fullname))
            yield resdef

    def _resource_node(self, resdef):
        if "sources" in resdef.data:
            return sources_node.SourcesNode(resdef, self)
        else:
            raise wf.DepError(
                "unknown resource type for '%s'" % resdef.name)

    def run(self):
        exit_status = self.op.proc(self.quiet)
        if exit_status != 0:
            raise wf.RunError("non-zero exit for run in %s" % self.op.run_dir)
