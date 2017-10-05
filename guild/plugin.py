import importlib
import os
import sys

PLUGIN_PACKAGES = [
    "guild.plugins",
]

__plugin_classes__ = None
__plugin_instances__ = {}

class Plugin(object):
    """Abstract interface for a Guild plugin."""

    name = None

    def project_models(self, project):
        pass

    def yyy(self):
        pass

def iter_plugins():
    """Returns an interation of available plugin names.

    Uses a list of plugin packages to enumerate named plugin
    classes. Plugin packages must provide a `__plugins__` attribute
    that is a map of plugin name to class name. Class must be string
    values consisting of either a fully qualified class name (fully
    qualified module + "." + class name) or relative class name
    (module name relative to the plugin package + "." + class name).

    See `guild/plugins/__init__.py` for an example.

    The list of plugin packages is not currently extensible and is
    limited to 'guild.plugins'. This will be modified as support for
    user-defined plugins is added.

    Use 'for_name' to return a plugin instance for an iteration value.

    """
    for name in __plugins__:
        yield name, __plugins__[name]

def for_name(name):
    """Returns a Guild plugin instance for a name.

    `init_plugins` must be called before calling this function.

    Name must be a valid plugin name as returned by `iter_plugins`.
    """
    return __plugins__[name]

def listen_method(method, cb):
    MethodWrapper.for_method(method).add_cb(cb)

def remove_method_listener(method, cb):
    MethodWrapper.for_method(method).remove_cb(cb)

def remove_method_listeners(method):
    MethodWrapper.unwrap(method)

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
