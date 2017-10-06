import importlib
import os
import sys
import time

PLUGIN_PACKAGES = [
    "guild.plugins",
]

__plugins__ = {}

class Plugin(object):
    """Abstract interface for a Guild plugin."""

    def init(self):
        pass

    def models_for_location(self, location):
        """Return a list or generator of models for location.

        A model must be a Python dict containing model attributes. See
        guild.project.Project for the expected structure.
        """
        return []

    def enabled_for_op(self, _op):
        return False

    def patch_env(self):
        pass

def init_plugins():
    for pkg in PLUGIN_PACKAGES:
        pkg_mod = importlib.import_module(pkg)
        plugins_map = getattr(pkg_mod, "__plugins__", {})
        for plugin_name, class_name in plugins_map.items():
            full_class_name = _full_class_name(pkg_mod, class_name)
            __plugins__[plugin_name] = _init_plugin(full_class_name)

def _full_class_name(pkg_mod, class_name):
    if class_name.startswith("."):
        return pkg_mod.__name__ + class_name
    else:
        return class_name

def _init_plugin(class_name):
    mod_name, class_attr = class_name.rsplit(".", 1)
    plugin_mod = importlib.import_module(mod_name)
    plugin_class = getattr(plugin_mod, class_attr)
    plugin = plugin_class()
    plugin.init()
    return plugin

def iter_plugins():
    """Returns an interation of available plugin names.

    `init_plugins` must be called before calling this function.

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
