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

import logging
import sys

from guild import cli
from guild import help

import guild.workflow as wf
import guild.workflow.op_node

log = logging.getLogger("guild")

def run(op, args):
    graph = _init_graph(op)
    if not args.yes:
        _preview(op, graph)
    if args.yes or _confirm():
        _run(graph)

def _init_graph(op):
    graph = wf.Graph()
    op_node = guild.workflow.op_node.OpNode(op)
    graph.add_node(op_node, with_deps=True)
    cycles = list(graph.cycles())
    assert not cycles, cycles
    return graph

def _preview(op, graph):
    out = help.ConsoleFormatter()
    out.write_text("You are about to run {}".format(op.opdef.fullname))
    if op.flag_vals:
        out.write_paragraph()
        out.write_subheading("Flags")
        out.indent()
        _write_flags(op.flag_vals, out)
        out.dedent()
    out.write_paragraph()
    out.write_subheading("Workflow")
    out.indent()
    _write_preview(graph, out)
    out.dedent()
    out.write_paragraph()
    if log.getEffectiveLevel() <= logging.DEBUG:
        out.write_subheading("Run sequence")
        out.indent()
        _write_sequence(graph, out)
        out.dedent()
        out.write_paragraph()
    sys.stderr.write("".join(out.buffer))

def _write_flags(flag_vals, out):
    out.write_dl([
        (name, str(flag_vals[name]))
        for name in sorted(flag_vals)
    ])

def _write_preview(graph, out):
    seen = set()
    for node in graph.preview_order():
        if node in seen:
            continue
        _write_preview_node(node, graph, out, seen)

def _write_preview_node(node, graph, out, seen):
    if node.user_detail_level < wf.MEDIUM:
        return
    seen.add(node)
    out.write_dl([("-", node.get_description())], col_spacing=1)
    out.indent()
    for dep in graph.node_deps(node):
        if dep in seen:
            continue
        _write_preview_node(dep, graph, out, seen)
    out.dedent()

def _write_sequence(graph, out):
    for node in graph.run_order():
        out.write_dl([("-", node.get_description())], col_spacing=1)

def _confirm():
    return cli.confirm("Continue?", default=True)

def _run(graph):
    for node in graph.run_order():
        node.run()
