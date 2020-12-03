# Copyright 2017-2020 TensorHub, Inc.
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

import ast
import json
import logging
import os

import six

from guild import config as configlib
from guild import flag_util
from guild import guildfile
from guild import model as modellib
from guild import plugin as pluginlib
from guild import python_util
from guild import util

log = logging.getLogger("guild")


class NotebookPlugin(pluginlib.Plugin):

    resolve_model_op_priority = 60

    def resolve_model_op(self, opspec):
        path = os.path.join(configlib.cwd(), opspec)
        if _is_notebook(path):
            model = NotebookModelProxy(path, opspec)
            return model, model.op_name
        return None

    def guildfile_loaded(self, gf):
        cache = {}
        for m in gf.models.values():
            for opdef in m.operations:
                if _is_nbexec_op(opdef):
                    _apply_notebook_flags(opdef, cache)


def _is_notebook(path):
    return os.path.isfile(path) and path.lower().endswith(".ipynb")


def _is_nbexec_op(opdef):
    return opdef.main and opdef.main.rstrip().startswith("guild.plugins.nbexec")


def _apply_notebook_flags(opdef, cache):
    notebook_path = _nbexec_notebook_path(opdef)
    if not notebook_path or not os.path.exists(notebook_path):
        return
    flags_data = _flags_data_for_notebook(notebook_path, cache)
    flag_util.apply_flags_data_to_op(flags_data, opdef)


def _nbexec_notebook_path(opdef):
    argv = util.shlex_split(opdef.main)
    assert argv and argv[0] == "guild.plugins.nbexec", (opdef.main, argv)
    if len(argv) > 1:
        return os.path.join(opdef.guildfile.dir, argv[1])
    return None


class NotebookModelProxy(object):

    name = ""

    def __init__(self, notebook_path, op_name):
        self.notebook_path = notebook_path
        if os.path.isabs(op_name) or op_name.startswith(".."):
            self.op_name = os.path.basename(op_name)
        else:
            self.op_name = op_name
        self.modeldef = _init_modeldef(self.notebook_path, self.name, self.op_name)
        script_base = notebook_path[: -len(self.op_name)]
        self.reference = modellib.script_model_ref(self.name, script_base)


def _init_modeldef(notebook_path, model_name, op_name):
    data = [
        {
            "model": model_name,
            "operations": {
                op_name: {
                    "main": "guild.plugins.nbexec %s" % notebook_path,
                    "flags": _flags_data_for_notebook(notebook_path),
                }
            },
        }
    ]
    gf = guildfile.Guildfile(data, dir=os.path.dirname(notebook_path))
    return gf.models[model_name]


def _flags_data_for_notebook(notebook_path, cache=None):
    cache = cache or {}
    try:
        return cache[notebook_path]
    except KeyError:
        data = dict(_iter_notebook_flag_data(notebook_path))
        return cache.setdefault(notebook_path, data)


def _iter_notebook_flag_data(notebook_path):
    for name, val in _iter_notebook_assigns(notebook_path):
        yield name, _flag_data_for_val(val)


def _iter_notebook_assigns(notebook_path):
    nb_data = _load_notebook(notebook_path)
    if not nb_data:
        return
    for src in _iter_notebook_source(nb_data):
        for _assign_node, target_node, _val_node, val in _iter_source_val_assigns(src):
            yield target_node.id, val


def _load_notebook(path):
    try:
        return json.load(open(path))
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("load notebook '%s'", path)
        else:
            log.warning("error loading notebook '%s': %s", path, e)
            return None


def _iter_notebook_source(nb_data):
    for cell in nb_data.get("cells", []):
        if cell.get("cell_type") == "code":
            yield "".join(cell.get("source", []))


def _iter_source_val_assigns(src):
    for node in _iter_source_assigns(src):
        try:
            val = python_util.ast_param_val(node.value)
        except TypeError:
            pass
        else:
            # Only support assigns to right-most name targets.
            target = node.targets[-1]
            if isinstance(target, ast.Name):
                yield node, target, node.value, val


def _iter_source_assigns(s):
    try:
        m = ast.parse(s)
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("parsing %r", s)
        else:
            log.warning("error parsing Python source %r: %s", s, e)
    else:
        for node in m.body:
            if isinstance(node, ast.Assign):
                yield node


def _flag_data_for_val(val):
    return {
        "default": val,
        "type": _flag_type(val),
    }


def _flag_type(val):
    if isinstance(val, six.string_types):
        return "string"
    elif isinstance(val, bool):
        return "boolean"
    elif isinstance(val, (int, float)):
        return "number"
    else:
        return None
