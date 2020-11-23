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

import warnings

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    import imp

import ast
import logging
import os
import re
import sys
import types

try:
    # pylint: disable=ungrouped-imports
    from ast import NameConstant
except ImportError:

    class FakeType(object):
        pass

    NameConstant = FakeType

log = logging.getLogger("guild")


class Script(object):
    def __init__(self, src, mod_package=None, sys_path=None):
        self.src = src
        self.name = _script_name(src)
        self.mod_package = mod_package
        self.sys_path = sys_path
        self._parsed = False
        self._imports = []
        self._calls = []
        self._params = {}
        self._parse()

    def __lt__(self, x):
        return self.__cmp__(x) < 0

    def __cmp__(self, x):
        return (self.src > x.src) - (self.src < x.src)

    @property
    def imports(self):
        return self._imports

    @property
    def calls(self):
        return self._calls

    @property
    def params(self):
        return self._params

    def _parse(self):
        assert not self._parsed
        parsed = ast.parse(open(self.src, "r").read())
        for node in ast.walk(parsed):
            self._safe_apply_node(node)
        self._parsed = True

    def _safe_apply_node(self, node):
        try:
            self._apply_node(node)
        except Exception as e:
            self._handle_apply_node_error(e, node)

    def _handle_apply_node_error(self, e, node):
        msg = "error applying AST node %s from %s:%s:" % (
            node.__class__.__name__,
            self.src,
            node.lineno,
        )
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception(msg)
        else:
            msg += " %s (use 'guild --debug ...' for more information)" % e
            log.warning(msg)

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
        if node.module:
            self._imports.append(node.module)
        if node.names:
            self._apply_import(node)

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
                if not isinstance(target, ast.Name):
                    continue
                self._params[target.id] = val


def _try_param_val(val):
    if isinstance(val, ast.Num):
        return val.n
    elif isinstance(val, ast.Str):
        return val.s
    elif isinstance(val, NameConstant):
        return val.value
    elif isinstance(val, ast.Name):
        if val.id == "True":
            return True
        elif val.id == "False":
            return False
        elif val.id == "None":
            return None
    elif isinstance(val, ast.List):
        return [_try_param_val(item) for item in val.elts]
    raise TypeError(val)


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
        def f(*args, **kw):
            self._func(wrapped_self, *args, **kw)

        f.__self__ = wrapped_self
        return f

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


def wrapped_self(method_wrapper):
    return method_wrapper.__self__


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


def exec_script(filename, globals=None, mod_name="__main__"):
    """Execute a Python script.

    This function can be used to execute a Python module as code
    rather than import it. Importing a module to execute it is not an
    option if importing has a side-effect of starting threads, in
    which case this function can be used.

    `mod_name` is ``__main__`` by default but may be an alternative
    module name. `mod_name` may include a package.

    Reference:

    https://docs.python.org/2/library/threading.html#importing-in-threaded-code

    """
    globals = globals or {}
    package_name, mod_name = split_mod_name(mod_name)
    _ensure_parent_mod_loaded(package_name)
    node_filter = _node_filter_for_globals(globals) if globals else None
    src = open(filename, "r").read()
    code = _compile_script(src, filename, node_filter)
    script_globals = dict(globals)
    script_globals.update(
        {
            "__package__": package_name,
            "__name__": mod_name,
            "__file__": filename,
        }
    )
    exec(code, script_globals)
    return script_globals


def split_mod_name(mod_name):
    parts = mod_name.split(".")
    return ".".join(parts[:-1]), parts[-1]


def _ensure_parent_mod_loaded(parent_mod_name):
    if parent_mod_name:
        try:
            __import__(parent_mod_name)
        except ValueError:
            assert False, parent_mod_name


def _node_filter_for_globals(globals):
    """Filters ast nodes in support of setting globals for exec.

    Removes initial assigns of any variables occuring in
    `globals`. This is to allow globals to provide the initial
    value. Subsequent assigns are not removed under the assumption
    that are re-defining the initial variable value.
    """
    names = set(globals.keys())
    removed = set()

    def f(node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if not isinstance(target, ast.Name) or target.id in removed:
                    return True
                if target.id in names:
                    removed.add(target.id)
                    return False
        return True

    return f


def _compile_script(src, filename, node_filter=None):
    import __future__

    ast_root = ast.parse(src, filename)
    if node_filter:
        ast_root = _filter_nodes(ast_root, node_filter)
    flags = __future__.absolute_import.compiler_flag
    return compile(ast_root, filename, "exec", flags=flags, dont_inherit=True)


def _filter_nodes(root, node_filter):
    if isinstance(root, (ast.Module, ast.If)):
        root.body = [
            _filter_nodes(node, node_filter) for node in root.body if node_filter(node)
        ]
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
        name == target_name
        and isinstance(val, target_type)
        and _match_ref_attrs(val, target_attrs)
    )


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


__modules = {}


def find_module(main_mod, model_paths):
    cache_key = (main_mod, tuple(model_paths))
    try:
        return __modules[cache_key]
    except KeyError:
        __modules[cache_key] = result = _find_module(main_mod, model_paths)
        return result


def _find_module(main_mod, model_paths):
    for model_path in model_paths:
        main_mod_sys_path, module = _split_module(main_mod, model_path)
        # Copied from guild.op_main
        parts = module.split(".")
        module_path = parts[0:-1]
        module_name_part = parts[-1]
        for sys_path_item in [main_mod_sys_path] + sys.path:
            cur_path = os.path.join(sys_path_item, *module_path)
            try:
                f, maybe_mod_path, _desc = imp.find_module(module_name_part, [cur_path])
            except ImportError:
                pass
            else:
                if f:
                    f.close()
                else:
                    maybe_mod_path = _find_package_main(maybe_mod_path)
                    if not maybe_mod_path:
                        raise ImportError(
                            "No module named %s.__main__ ('%s' is a package "
                            "and cannot be directly executed)" % (module, module)
                        )
                return main_mod_sys_path, maybe_mod_path
    raise ImportError("No module named %s" % main_mod)


def _find_package_main(mod_path):
    names = ["__main__.py", "__main__.pyc"]
    for name in names:
        path = os.path.join(mod_path, name)
        if os.path.exists(path):
            return path
    return None


def _split_module(main_mod, gf_dir):
    parts = main_mod.rsplit("/", 1)
    if len(parts) == 1:
        parts = ".", parts[0]
    return os.path.join(gf_dir, parts[0]), parts[1]


def test_package_version(version, req):
    req = _parse_req(req)
    matches = list(req.specifier.filter({version: ""}, prereleases=True))
    return len(matches) > 0


def _parse_req(req):
    import pkg_resources

    req = _apply_equals(req)
    try:
        return pkg_resources.Requirement.parse("notused%s" % req)
    except Exception as e:
        raise ValueError(e)


def _apply_equals(req):
    return ",".join([_apply_equals2(part) for part in req.split(",")])


def _apply_equals2(s):
    if re.match(r"^\d", s):
        return "==%s" % s
    return s


def first_breakable_line(src):
    return next_breakable_line(src, 1)


def next_breakable_line(src, line=1):
    """Returns the next breaking line in a Python module.

    Pdb breakpoints require non-expression lines to take
    effect. I.e. they require something to execute. A non-breakable
    line is ignored.

    This function returns the next breakable line starting with
    `line`. If `line` is breakable, it is returned.

    If `src` is not a valid Python module or the module doesn't
    contain a breakable line, the function raises TypeError.
    """
    parsed = ast.parse(open(src, "r").read())
    for lineno in _iter_breakable_lines(parsed):
        if lineno >= line:
            return lineno
    raise TypeError("no breakable lines at or after %i in %s" % (line, src))


def _iter_breakable_lines(top):
    for node in ast.walk(top):
        if node is top:
            continue
        line = getattr(node, "lineno", None)
        if line is None:
            continue
        if _is_node_breakable(node):
            yield line
        for line in _iter_breakable_lines(node):
            yield line


NON_BREAKABLE_NODE_TYPES = set(
    [
        ast.Expr,
        ast.Str,
        ast.Num,
        ast.List,
        ast.Dict,
        ast.Tuple,
        ast.Set,
        ast.Name,
    ]
)

try:
    NON_BREAKABLE_NODE_TYPES.add(ast.Constant)
except AttributeError:
    pass


def _is_node_breakable(node):
    # pylint: disable=unidiomatic-typecheck
    return type(node) not in NON_BREAKABLE_NODE_TYPES
