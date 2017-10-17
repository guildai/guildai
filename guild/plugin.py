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

__plugins = None

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
        log("plugin '%s' %s" % (self.name, msg), *args, **kw)

def _plugins():
    if __plugins is not None:
        return __plugins
    globals()["__plugins"] = plugins = _init_plugins()
    return plugins

class UnresolvedPlugin(object):

    def __init__(self, ep):
        self._ep = ep

    def resolve(self):
        plugin = self._ep.resolve()()
        plugin.name = self._ep.name
        plugin.init()
        return plugin

    def __str__(self):
        parts = [self._ep.module_name]
        if self._ep.attrs:
            parts.extend([":", ".".join(self._ep.attrs)])
        if self._ep.extras:
            parts.extend([" [", ','.join(self._ep.extras), "]"])
        return "".join(parts)

def _init_plugins():
    """Returns a map of plugin name to UnresolvedPlugin.

    Guild's plugin scheme uses entry points in group "guild.plugins"
    to lookup available plugins. There should be one plugin per name
    registered. This init algorithm does not consider the case where
    there is more than one plugin with the same name. In that case,
    the selected process is undefined.
    """
    import pkg_resources # expensive
    return {
        ep.name: UnresolvedPlugin(ep)
        for ep in pkg_resources.iter_entry_points("guild.plugins")
    }

def iter_plugins():
    for name in _plugins():
        yield name, for_name(name)

def for_name(name):
    """Returns a Guild plugin instance for a name.

    Name must be a valid plugin name as returned by `iter_plugins`.
    """
    plugins = _plugins()
    try:
        plugin = plugins[name]
    except KeyError:
        raise LookupError(name)
    else:
        if isinstance(plugin, UnresolvedPlugin):
            logging.debug("initializing plugin '%s' (%s)", name, plugin)
            plugins[name] = plugin = plugin.resolve()
        return plugin

def _init_plugin(class_name, name):
    mod_name, class_attr = class_name.rsplit(".", 1)
    plugin_mod = importlib.import_module(mod_name)
    plugin_class = getattr(plugin_mod, class_attr)
    plugin = plugin_class()
    plugin.name = name
    plugin.init()
    return plugin
