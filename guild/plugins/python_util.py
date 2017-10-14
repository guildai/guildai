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

import ast
import logging
import os
import sys

if sys.version_info[0] == 2:
    def _im_func(m):
        return m.im_func

    def _im_class(m):
        return m.im_class
else:
    def _im_func(m):
        return m.__func__

    def _im_class(m):
        return m.__self__.__class__

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

    # pylint: disable=protected-access

    @staticmethod
    def for_method(m):
        wrapper = getattr(_im_func(m), "__method_wrapper__", None)
        return wrapper if wrapper else MethodWrapper(m)

    @staticmethod
    def unwrap(m):
        wrapper = getattr(_im_func(m), "__method_wrapper__", None)
        if wrapper:
            wrapper._unwrap()

    def __init__(self, m):
        self._m = m
        self._cbs = []
        self._wrap()

    def _wrap(self):
        wrapper = self._wrapper()
        name = _im_func(self._m).__name__
        wrapper.__name__ = "%s_wrapper" % name
        wrapper.__method_wrapper__ = self
        setattr(_im_class(self._m), name, wrapper)

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
                except:
                    logging.exception("callback")
            return (wrapped_bound(*args, **kw)
                    if result is marker
                    else result)
        return wrapper

    def _bind(self, wrapped_self):
        return lambda *args, **kw: self._m(wrapped_self, *args, **kw)

    def add_cb(self, cb):
        self._cbs.append(cb)

    def remove_cb(self, cb):
        try:
            self._cbs.remove(cb)
        except ValueError:
            pass
        if not self._cbs:
            self._unwrap()

    def _unwrap(self):
        setattr(_im_class(self._m), _im_func(self._m).__name__, self._m)

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

def listen_method(method, cb):
    MethodWrapper.for_method(method).add_cb(cb)

def remove_method_listener(method, cb):
    MethodWrapper.for_method(method).remove_cb(cb)

def remove_method_listeners(method):
    MethodWrapper.unwrap(method)

def exec_script(filename):
    import __future__
    src = open(filename, "r").read()
    flags = __future__.absolute_import.compiler_flag
    code = compile(src, filename, "exec", flags=flags, dont_inherit=True)
    exec(code)
