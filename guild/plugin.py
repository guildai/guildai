import importlib
import os
import sys

PLUGIN_PACKAGES = [
    "guild.plugins",
]

class Plugin(object):
    """Abstract interface for a Guild plugin."""

    name = None

    def project_models(self, project):
        pass

    def yyy(self):
        pass

def iter_plugins():
    """Iterates Guild plugins.

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

    Each iteration yields a tuple of name and fully qualified class
    name. Use `plugin` to create an instance of a plugin
    using the class name returned by this function.
    """
    for pkg in PLUGIN_PACKAGES:
        try:
            pkg_mod = importlib.import_module(pkg)
        except ImportError:
            logging.exception("plugin package: " % pkg)
        else:
            plugins_map = getattr(pkg_mod, "__plugins__", {})
            for plugin_name, class_name in plugins_map.items():
                yield plugin_name, _full_class_name(pkg_mod, class_name)

def _full_class_name(pkg_mod, class_name):
    if class_name.startswith("."):
        return pkg_mod.__name__ + class_name
    else:
        return class_name

def plugin(class_name):
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
