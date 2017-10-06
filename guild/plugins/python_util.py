import ast
import glob
import logging
import os

class Script(object):

    def __init__(self, src):
        self.src = src
        self.name = _script_name(src)
        self._parsed = None

    def __cmp__(self, x):
        return cmp(self.src, x.src) if isinstance(x, Script) else -1

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
                logging.exception("parsing %s", src)
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
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            raise AssertionError(node)
        parts.append(node.id)
        return ".".join(reversed(parts))

def _script_name(src):
    basename = os.path.basename(src)
    name, _ = os.path.splitext(basename)
    return name

class MethodWrapper(object):

    @staticmethod
    def for_method(m):
        wrapper = getattr(m.im_func, "__method_wrapper__", None)
        return wrapper if wrapper else MethodWrapper(m)

    @staticmethod
    def unwrap(m):
        wrapper = getattr(m.im_func, "__method_wrapper__", None)
        if wrapper:
            wrapper._unwrap()

    def __init__(self, m):
        self._m = m
        self._cbs = []
        self._wrap()

    def _wrap(self):
        wrapper = self._wrapper()
        name = self._m.im_func.__name__
        wrapper.__name__ = "%s_wrapper" % name
        wrapper.__method_wrapper__ = self
        setattr(self._m.im_class, name, wrapper)

    def _wrapper(self):
        def wrapper(wrapped_self, *args, **kw):
            wrapped_bound = self._bind(wrapped_self)
            call_wrapped = True
            for cb in self._cbs:
                try:
                    cb_result = cb(wrapped_bound, *args, **kw)
                except KeyboardInterrupt:
                    raise
                except:
                    import logging
                    logging.exception("callback error")
                else:
                    call_wrapped = call_wrapped and not cb_result is False
            if call_wrapped:
                wrapped_bound(*args, **kw)
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
        setattr(self._m.im_class, self._m.im_func.__name__, self._m)

def scripts_for_location(location):
    return [
        Script(src)
        for src in glob.glob(os.path.join(location, "*.py"))
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
