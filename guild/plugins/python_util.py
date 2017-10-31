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

import ast
import logging
import os
import types

class Script(object):

    def __init__(self, src):
        self.src = src
        self.name = _script_name(src)
        self._parsed = None

    def __lt__(self, x):
        return self.__cmp__(x) < 0

    def __cmp__(self, x):
        return (self.src > x.src) - (self.src < x.src)

    def imports(self):
        self._ensure_parsed()
        return self._parsed.get("imports", [])

    def calls(self):
        self._ensure_parsed()
        return self._parsed.get("calls", [])

    def _ensure_parsed(self):
        if self._parsed is None:
            self._parsed = {}
            try:
                parsed = ast.parse(open(self.src, "r").read())
            except SyntaxError:
                logging.exception("parsing %s", self.src)
            else:
                for node in ast.walk(parsed):
                    self._apply_node(node)

    def _apply_node(self, node):
        if isinstance(node, ast.ImportFrom):
            self._apply_import_from(node)
        elif isinstance(node, ast.Import):
            self._apply_import(node)
        elif isinstance(node, ast.Call):
            self._apply_call(node)

    def _apply_import_from(self, node):
        imports = self._parsed.setdefault("imports", [])
        imports.append(node.module)

    def _apply_import(self, node):
        imports = self._parsed.setdefault("imports", [])
        for name in node.names:
            if isinstance(name, ast.alias):
                imports.append(name.name)

    def _apply_call(self, node):
        calls = self._parsed.setdefault("calls", [])
        calls.append(Call(node))

class Call(object):

    def __init__(self, node):
        if isinstance(node.func, ast.Name):
            self.name = node.func.id
            self.path = self.name
        elif isinstance(node.func, ast.Attribute):
            self.name = node.func.attr
            self.path = self._call_path(node.func)
        else:
            raise AssertionError(node.func)

    @staticmethod
    def _call_path(node):
        parts = []
        while True:
            if isinstance(node, ast.Attribute):
                parts.append(node.attr)
                node = node.value
            elif isinstance(node, ast.Call):
                parts.append("%s()" % node.func.attr)
                node = node.func.value
            elif isinstance(node, ast.Name):
                parts.append(node.id)
                break
            else:
                raise AssertionError(node)
        return ".".join(reversed(parts))

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

def scripts_for_location(location, exclude=None):
    import glob
    import fnmatch
    exclude = [] if exclude is None else exclude
    return [
        Script(src)
        for src in glob.glob(os.path.join(location, "*.py"))
        if not any((fnmatch.fnmatch(src, pattern) for pattern in exclude))
    ]

def script_models(location, is_model_script, script_model):
    for script in sorted(scripts_for_location(location)):
        if is_model_script(script):
            yield script_model(script)

def exec_script(filename):
    import __future__
    src = open(filename, "r").read()
    flags = __future__.absolute_import.compiler_flag
    code = compile(src, filename, "exec", flags=flags, dont_inherit=True)
    exec(code)

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
