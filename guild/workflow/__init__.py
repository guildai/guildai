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

import networkx as nx

class RunError(RuntimeError):
    pass

class Graph(object):

    def __init__(self):
        self._g = nx.DiGraph()

    def add_node(self, node, with_deps=False):
        self._g.add_node(node)
        if with_deps:
            for dep in node.get_deps():
                self.add_node(dep, with_deps=True)
                self.add_dep(dep, node)

    def add_dep(self, dep, node):
        self._g.add_edge(dep, node)

    def add_deps(self, deps, node):
        self._g.add_edges_from([(dep, node) for dep in deps])

    def run_order(self):
        return nx.topological_sort(self._g)

class Node(object):

    def get_description(self):
        raise NotImplementedError()

    @staticmethod
    def get_deps():
        return []

    def run(self):
        raise NotImplementedError()
