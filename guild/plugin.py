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

import logging

from . import entry_point_util

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

def _init_plugin(plugin, ep):
    plugin.name = ep.name
    plugin.init()

_plugins = entry_point_util.EntryPointResources(
    "guild.plugins", "plugin", _init_plugin)

iter_plugins = _plugins.__iter__

for_name = _plugins.one_for_name
