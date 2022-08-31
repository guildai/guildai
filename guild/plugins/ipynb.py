# Copyright 2017-2022 RStudio, PBC
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

import ast
import json
import logging
import os
import re

from guild import config as configlib
from guild import guildfile
from guild import model as modellib
from guild import plugin as pluginlib
from guild import python_util
from guild import util

from . import flags_import_util

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
                _maybe_apply_main(opdef)
                _maybe_apply_notebook_flags(opdef, cache)


def _is_notebook(path):
    return os.path.isfile(path) and path.lower().endswith(".ipynb")


def _maybe_apply_main(opdef):
    if opdef.name.lower().endswith(".ipynb") and not opdef.main:
        opdef.main = f"guild.plugins.nbexec {opdef.name}"


def _maybe_apply_notebook_flags(opdef, cache):
    if _is_nbexec_op(opdef):
        _apply_notebook_flags(opdef, cache)


def _is_nbexec_op(opdef):
    return opdef.main and opdef.main.lstrip().startswith("guild.plugins.nbexec")


def _apply_notebook_flags(opdef, cache):
    notebook_path = _nbexec_notebook_path(opdef)
    if not notebook_path or not os.path.exists(notebook_path):
        return
    flags_import_util.apply_flags(
        opdef, lambda: _flags_data_for_notebook(notebook_path, opdef, cache)
    )


def _nbexec_notebook_path(opdef):
    argv = util.shlex_split(opdef.main)
    assert argv and argv[0] == "guild.plugins.nbexec", (opdef.main, argv)
    if len(argv) > 1:
        return os.path.join(opdef.guildfile.dir, argv[1])
    return None


class NotebookModelProxy:

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
                    "main": f"guild.plugins.nbexec {_normpath_for_main(notebook_path)}",
                    "flags": _flags_data_for_notebook(notebook_path),
                }
            },
        }
    ]
    gf = guildfile.Guildfile(data, dir=os.path.dirname(notebook_path))
    return gf.models[model_name]


def _normpath_for_main(path):
    """Normalize path for use in operation main spec.

    Guild does not support Windows style backslashes in op main specs
    so we normalize to forward slash.
    """
    return path.replace(os.path.sep, "/")


def _flags_data_for_notebook(notebook_path, opdef=None, cache=None):
    cache = cache or {}
    try:
        return cache[notebook_path]
    except KeyError:
        data = dict(_iter_notebook_flag_data(notebook_path, opdef))
        return cache.setdefault(notebook_path, data)


def _iter_notebook_flag_data(notebook_path, opdef=None):
    """Iterator that returns name, flag_data for notebooks flags.

    Notebook flag data is derrived from inspecting the notebook for
    global assigns and by applying replacement patterns optionally
    provided by operation flag defs.

    If opdef is provided and a flag provides a replacement patter, it
    takes precedence over values from global assigns.
    """
    seen = set()
    if opdef:
        for name, val in _iter_notebook_flag_replacements(notebook_path, opdef):
            yield name, _flag_data_for_val(val)
            seen.add(name)
    for name, val, ann_type in _iter_notebook_assigns(notebook_path):
        if not name in seen:
            yield name, _flag_data_for_val(val, ann_type)


def _iter_notebook_flag_replacements(notebook_path, opdef):
    nb_data = _load_notebook(notebook_path)
    if not nb_data:
        return
    for src in _iter_notebook_source(nb_data):
        for name, val in _iter_replacements_for_source(src, opdef):
            yield name, val


def _iter_replacements_for_source(src, opdef):
    for flagdef in opdef.flags:
        nb_replace = flagdef.extra.get("nb-replace")
        if not nb_replace:
            continue
        try:
            m = re.search(nb_replace, src, re.MULTILINE)
        except ValueError:
            pass
        else:
            if m and m.regs:
                val_str = _replacement_capture(m, src)
                try:
                    # pylint: disable=eval-used
                    val = eval(val_str)
                except Exception as e:
                    if log.getEffectiveLevel() < logging.DEBUG:
                        log.exception("evaluating captured string %r", val_str)
                    else:
                        log.warning("cannot decode captured string %r: %s", val_str, e)
                else:
                    yield flagdef.name, val


def _replacement_capture(m, s):
    start_slice, end_slice = _replacement_capture_slice(m)
    return s[start_slice:end_slice]


def _replacement_capture_slice(m):
    if len(m.regs) == 1:
        # If no capture groups, assume entire capture.
        return m.regs[0]
    return m.regs[1]


def _iter_notebook_assigns(notebook_path):
    nb_data = _load_notebook(notebook_path)
    if not nb_data:
        return
    for src in _iter_notebook_source(nb_data):
        try:
            src = _ipython_to_python(src)
        except MissingIPython:
            break
        else:
            for (
                _assign_node,
                target_node,
                _val_node,
                val,
                ann_type,
            ) in _iter_source_val_assigns(src):
                yield target_node.id, val, ann_type


class MissingIPython(Exception):
    pass


def _ipython_to_python(source):
    try:
        from IPython.core.inputsplitter import IPythonInputSplitter
    except ImportError as e:
        log.warning(
            "IPython is required to process Notebook source code - "
            "install it by running 'pip install ipython'"
        )
        raise MissingIPython() from e
    else:
        isp = IPythonInputSplitter(line_input_checker=False)
        python_source = isp.transform_cell(source)
        return _fix_ipython_to_python_lf(python_source, source)


def _fix_ipython_to_python_lf(ipython_s, python_s):
    if python_s[-1:] != "\n" and ipython_s[-1:] == "\n":
        return ipython_s[:-1]
    return ipython_s


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
            target = _assign_node_target(node)
            ann_type = _assign_node_ann_type(node)
            if isinstance(target, ast.Name):
                yield node, target, node.value, val, ann_type


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
            if _is_assign(node):
                yield node


def _is_assign(node):
    if isinstance(node, ast.Assign):
        return True
    if hasattr(ast, "AnnAssign") and isinstance(node, ast.AnnAssign):
        return True
    return False


def _assign_node_target(node):
    if hasattr(node, "targets"):
        # Only support assigns to right-most name targets.
        return node.targets[-1]
    if hasattr(node, "target"):
        return node.target
    assert False, node


def _assign_node_ann_type(node):
    if hasattr(node, "annotation"):
        return _flag_type_for_annotation(node.annotation)
    return None


def _flag_type_for_annotation(ann):
    if not isinstance(ann, ast.Name):
        return None
    if ann.id == "int":
        return "int"
    if ann.id == "float":
        return "float"
    if ann.id == "bool":
        return "boolean"
    if ann.id == "str":
        return "string"
    return None


def _flag_data_for_val(val, ann_type=None):
    return {
        "default": val,
        "type": ann_type or _flag_type(val),
    }


def _flag_type(val):
    if isinstance(val, str):
        return "string"
    if isinstance(val, bool):
        return "boolean"
    if isinstance(val, (int, float)):
        return "number"
    return None
