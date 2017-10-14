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

import importlib
import logging

PLUGIN_PACKAGES = [
    "guild.plugins",
]

__plugins__ = {}

class NotSupported(Exception):
    pass

class Plugin(object):
    """Abstract interface for a Guild plugin."""

    # pylint: disable=no-self-use

    name = None

    def init(self):
        pass

    def models_for_location(self, _location):
        """Return a list or generator of models for location.

        A model must be a Python dict containing model attributes. See
        guild.project.Project for the expected structure.
        """
        return []

    def enabled_for_op(self, _op):
        return False

    def run_op(self, op_spec, args):
        """The plugin should run the specified operation.

        Raises NotSupported if the plugin doesn't support the
        operation.
        """
        raise NotSupported(op_spec, args)

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
            plugin = _init_plugin(plugin, name)
            __plugins__[name] = plugin
        return plugin

def _init_plugin(class_name, name):
    mod_name, class_attr = class_name.rsplit(".", 1)
    plugin_mod = importlib.import_module(mod_name)
    plugin_class = getattr(plugin_mod, class_attr)
    plugin = plugin_class()
    plugin.name = name
    plugin.init()
    return plugin
