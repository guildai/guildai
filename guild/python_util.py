# Copyright 2017-2019 TensorHub, Inc.
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
import logging
import os
import re
import types

log = logging.getLogger("guild")

class Script(object):

    def __init__(self, src):
        self.src = src
        self.name = _script_name(src)
        self._parsed = False
        self._imports = []
        self._calls = []
        self._params = {}

    def __lt__(self, x):
        return self.__cmp__(x) < 0

    def __cmp__(self, x):
        return (self.src > x.src) - (self.src < x.src)

    @property
    def imports(self):
        self._ensure_parsed()
        return self._imports

    @property
    def calls(self):
        self._ensure_parsed()
        return self._calls

    @property
    def params(self):
        self._ensure_parsed()
        return self._params

    def _ensure_parsed(self):
        if not self._parsed:
            try:
                parsed = ast.parse(open(self.src, "r").read())
            except SyntaxError:
                log.exception("parsing %s", self.src)
            else:
                for node in ast.walk(parsed):
                    self._apply_node(node)
            self._parsed = True

    def _apply_node(self, node):
        if isinstance(node, ast.ImportFrom):
            self._apply_import_from(node)
        elif isinstance(node, ast.Import):
            self._apply_import(node)
        elif isinstance(node, ast.Call):
            self._maybe_apply_call(node)
        elif isinstance(node, ast.Assign):
            self._apply_assign(node)

    def _apply_import_from(self, node):
        self._imports.append(node.module)

    def _apply_import(self, node):
        for name in node.names:
            if isinstance(name, ast.alias):
                self._imports.append(name.name)

    def _maybe_apply_call(self, node):
        call = Call(node)
        if call.name:
            self._calls.append(call)

    def _apply_assign(self, node):
        if node.col_offset == 0:
            self._try_apply_param(node)

    def _try_apply_param(self, node):
        try:
            val = _try_param_val(node.value)
        except TypeError:
            pass
        else:
            for target in node.targets:
                self._params[target.id] = val

def _try_param_val(val):
    if isinstance(val, ast.Num):
        return val.n
    elif isinstance(val, ast.Str):
        return val.s
    elif isinstance(val, ast.Name):
        if val.id == "True":
            return True
        elif val.id == "False":
            return False
        elif val.id == "None":
            return None
    raise TypeError()

class Call(object):

    def __init__(self, node):
        self.node = node
        self.name = self._func_name(node.func)

    def _func_name(self, func):
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            return func.attr
        elif isinstance(func, ast.Call):
            return self._func_name(func.func)
        elif isinstance(func, ast.Subscript):
            return None
        else:
            raise AssertionError(func)

    def kwarg_param(self, name):
        for kw in self.node.keywords:
            if kw.arg == name:
                try:
                    _try_param_val(kw.value)
                except TypeError:
                    return None
        return None

def _script_name(src):
    basename = os.path.basename(src)
    name, _ = os.path.splitext(basename)
    return name

class Result(Exception):

    def __init__(self, value):
        super(Result, self).__init__(value)
        self.value = value

class MethodWrapper(object):

    @staticmethod
    def for_method(method):
        return getattr(method, "__wrapper__", None)

    def __init__(self, func, cls, name):
        self._func = func
        self._cls = cls
        self._name = name
        self._cbs = []
        self._wrap()

    def _wrap(self):
        wrapper = self._wrapper()
        wrapper.__name__ = "%s_wrapper" % self._name
        wrapper.__wrapper__ = self
        setattr(self._cls, self._name, wrapper)

    def _wrapper(self):
        def wrapper(wrapped_self, *args, **kw):
            wrapped_bound = self._bind(wrapped_self)
            marker = object()
            result = marker
            for cb in self._cbs:
                try:
                    cb(wrapped_bound, *args, **kw)
                except Result as e:
                    result = e.value
                except KeyboardInterrupt:
                    raise
            if result is marker:
                return wrapped_bound(*args, **kw)
            else:
                return result
        return wrapper

    def _bind(self, wrapped_self):
        return lambda *args, **kw: self._func(wrapped_self, *args, **kw)

    def add_cb(self, cb):
        self._cbs.append(cb)

    def remove_cb(self, cb):
        try:
            self._cbs.remove(cb)
        except ValueError:
            pass
        if not self._cbs:
            self.unwrap()

    def unwrap(self):
        setattr(self._cls, self._name, self._func)

def listen_method(cls, method_name, cb):
    method = getattr(cls, method_name)
    wrapper = MethodWrapper.for_method(method)
    if wrapper is None:
        wrapper = MethodWrapper(method, cls, method_name)
    wrapper.add_cb(cb)

def remove_method_listener(method, cb):
    wrapper = MethodWrapper.for_method(method)
    if wrapper is not None:
        wrapper.remove_cb(cb)

def remove_method_listeners(method):
    wrapper = MethodWrapper.for_method(method)
    if wrapper is not None:
        wrapper.unwrap()

class FunctionWrapper(object):

    @staticmethod
    def for_function(function):
        return getattr(function, "__wrapper__", None)

    def __init__(self, func, mod, name):
        self._func = func
        self._mod = mod
        self._name = name
        self._cbs = []
        self._wrap()

    def _wrap(self):
        wrapper = self._wrapper()
        wrapper.__name__ = "%s_wrapper" % self._name
        wrapper.__wrapper__ = self
        setattr(self._mod, self._name, wrapper)

    def _wrapper(self):
        def wrapper(*args, **kw):
            marker = object()
            result = marker
            for cb in self._cbs:
                try:
                    cb(self._func, *args, **kw)
                except Result as e:
                    result = e.value
                except KeyboardInterrupt:
                    raise
            if result is marker:
                return self._func(*args, **kw)
            else:
                return result
        return wrapper

    def add_cb(self, cb):
        self._cbs.append(cb)

    def remove_cb(self, cb):
        try:
            self._cbs.remove(cb)
        except ValueError:
            pass
        if not self._cbs:
            self.unwrap()

    def unwrap(self):
        setattr(self._mod, self._name, self._func)

def listen_function(module, function_name, cb):
    function = getattr(module, function_name)
    wrapper = FunctionWrapper.for_function(function)
    if wrapper is None:
        wrapper = FunctionWrapper(function, module, function_name)
    wrapper.add_cb(cb)

def remove_function_listener(function, cb):
    wrapper = FunctionWrapper.for_function(function)
    if wrapper is not None:
        wrapper.remove_cb(cb)

def remove_function_listeners(function):
    wrapper = FunctionWrapper.for_function(function)
    if wrapper is not None:
        wrapper.unwrap()

def scripts_for_dir(dir, exclude=None):
    import glob
    import fnmatch
    exclude = [] if exclude is None else exclude
    return [
        Script(src)
        for src in glob.glob(os.path.join(dir, "*.py"))
        if not any((fnmatch.fnmatch(src, pattern) for pattern in exclude))
    ]

def exec_script(filename, globals):
    """Execute a Python script.

    This function can be used to execute a Python module as code
    rather than import it. Importing a module to execute it is not an
    option if importing has a side-effect of starting threads, in
    which case this function can be used.

    Reference:

    https://docs.python.org/2/library/threading.html#importing-in-threaded-code

    """
    src = open(filename, "r").read()
    code = _compile_script(src, filename, _node_filter(globals))
    script_globals = dict(globals)
    script_globals.update({
        "__name__": "__main__",
        "__file__": filename,
    })
    exec(code, script_globals)

def _node_filter(globals):
    names = globals.keys()
    def f(node):
        if isinstance(node, ast.Assign):
            return not any(
                t.id in names
                for t in node.targets
                if isinstance(t, ast.Name))
        elif isinstance(node, ast.FunctionDef):
            return node.name not in names
        return True
    return f

def _compile_script(src, filename, node_filter):
    import __future__
    ast_root = ast.parse(src, filename)
    ast_root = _filter_nodes(ast_root, node_filter)
    flags = __future__.absolute_import.compiler_flag
    return compile(ast_root, filename, "exec", flags=flags, dont_inherit=True)

def _filter_nodes(root, node_filter):
    if isinstance(root, (ast.Module, ast.If)):
        root.body = [
            _filter_nodes(node, node_filter)
            for node in root.body
            if node_filter(node)]
    return root

def update_refs(module, ref_spec, new_val, recurse=False, seen=None):
    seen = seen or set()
    if module in seen:
        return
    seen.add(module)
    for name, val in module.__dict__.items():
        if _match_ref(name, val, ref_spec):
            module.__dict__[name] = new_val
        elif recurse and isinstance(val, types.ModuleType):
            update_refs(val, ref_spec, new_val, recurse, seen)

def _match_ref(name, val, ref_spec):
    target_name, target_type, target_attrs = ref_spec
    return (
        name == target_name and
        isinstance(val, target_type) and
        _match_ref_attrs(val, target_attrs))

def _match_ref_attrs(val, attrs):
    undef = object()
    return all((getattr(val, name, undef) == attrs[name] for name in attrs))

def is_python_script(opspec):
    return os.path.isfile(opspec) and opspec[-3:] == ".py"

def script_module(script_path, cwd="."):
    mod_path = os.path.splitext(script_path)[0]
    return os.path.relpath(mod_path, cwd)

def safe_module_name(s):
    if s.lower().endswith(".py"):
        s = s[:-3]
    return re.sub("-", "_", s)
