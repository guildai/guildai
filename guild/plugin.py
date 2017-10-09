import importlib
import logging
import os
import sys
import time

import guild.run

PLUGIN_PACKAGES = [
    "guild.plugins",
]

__plugins__ = {}

class Plugin(object):
    """Abstract interface for a Guild plugin."""

    name = None

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

    def run_op(self, name, _args):
        raise NotImplementedError(name)

    def patch_env(self):
        pass

    def log(self, msg, *args, **kw):
        if kw.get("exception"):
            log = logging.exception
        elif kw.get("error"):
            log = logging.error
        elif kw.get("warning"):
            log = logging.warn
        elif kw.get("info"):
            log = logging.info
        else:
            log = logging.debug
        log("[%s] %s" % (self.name, msg), *args, **kw)

def init_plugins():
    """Called by system to initialize the list of available plugins.

    This function must be called prior to using `iter_plugins` or
    `for_name`.
    """
    for pkg in PLUGIN_PACKAGES:
        pkg_mod = importlib.import_module(pkg)
        plugins_map = getattr(pkg_mod, "__plugins__", {})
        for plugin_name, class_name in plugins_map.items():
            __plugins__[plugin_name] = _full_class_name(pkg_mod, class_name)

def _full_class_name(pkg_mod, class_name):
    if class_name.startswith("."):
        return pkg_mod.__name__ + class_name
    else:
        return class_name

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
        yield name, for_name(name)

def for_name(name):
    """Returns a Guild plugin instance for a name.

    `init_plugins` must be called before calling this function.

    Name must be a valid plugin name as returned by `iter_plugins`.
    """
    try:
        plugin = __plugins__[name]
    except KeyError:
        raise LookupError(name)
    else:
        if isinstance(plugin, str):
            logging.debug("initializing plugin '%s' (%s)", name, plugin)
            plugin = _init_plugin(plugin)
            plugin.name = name
            __plugins__[name] = plugin
        return plugin

def _init_plugin(class_name):
    mod_name, class_attr = class_name.rsplit(".", 1)
    plugin_mod = importlib.import_module(mod_name)
    plugin_class = getattr(plugin_mod, class_attr)
    plugin = plugin_class()
    plugin.init()
    return plugin

def exit(msg, exit_status=1):
    """Exit the Python runtime with a message.
    """
    sys.stderr.write(msg)
    sys.stderr.write("\n")
    sys.exit(exit_status)

class NoCurrentRun(Exception):
    pass

def current_run():
    """Returns an instance of guild.run.Run for the current run.

    The current run directory must be specified with the RUNDIR
    environment variable. If this variable is not defined, raised
    NoCurrentRun.
    """
    path = os.getenv("RUNDIR")
    if not path:
        raise NoCurrentRun()
    run_id = os.path.basename(path)
    return guild.run.Run(run_id, path)
