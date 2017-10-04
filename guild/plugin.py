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
    _ensure_plugin_classes()
    return iter(__plugin_classes__)

def _ensure_plugin_classes():
    global __plugin_classes__
    if __plugin_classes__ is not None:
        return
    __plugin_classes__ = {}
    for pkg in PLUGIN_PACKAGES:
        try:
            pkg_mod = importlib.import_module(pkg)
        except ImportError:
            logging.exception("plugin package: " % pkg)
        else:
            plugins_map = getattr(pkg_mod, "__plugins__", {})
            for plugin_name, class_name in plugins_map.items():
                full_class_name = _full_class_name(pkg_mod, class_name)
                __plugin_classes__[plugin_name] = full_class_name

def _full_class_name(pkg_mod, class_name):
    if class_name.startswith("."):
        return pkg_mod.__name__ + class_name
    else:
        return class_name

def for_name(name):
    """Returns a Guild plugin instance for a name.

    Name must be a valid plugin name as returned by `iter_plugins`.
    """
    try:
        return __plugin_instances__[name]
    except KeyError:
        _ensure_plugin_classes()
        plugin_class = __plugin_classes__[name]
        plugin = _for_class(plugin_class)
        __plugin_instances__[name] = plugin
        return plugin

def _for_class(class_name):
    """Returns a Guild plugin instance for a class name.

    Class names must be full qualified class names consisting of a
    fully qualified module name + "." + class name.

    Raises ImportError if an error occurs loading the class module.

    Raises AttributeError if the plugin class is not defined in the
    class module.

    """
    mod_name, class_attr = class_name.rsplit(".", 1)
    plugin_mod = importlib.import_module(mod_name)
    plugin_class = getattr(plugin_mod, class_attr)
    return plugin_class()
