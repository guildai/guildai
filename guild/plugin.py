# Copyright 2017-2018 TensorHub, Inc.
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

from guild import __pkgdir__
from guild import entry_point_util

_plugins = entry_point_util.EntryPointResources("guild.plugins", "plugin")

class NotSupported(TypeError):
    pass

class Plugin(object):
    """Abstract interface for a Guild plugin."""

    # pylint: disable=no-self-use

    name = None

    def __init__(self, ep):
        self.name = ep.name
        self.log = logging.getLogger("guild." + self.name)

    def find_models(self, _path):
        """Return an iterator of models for path.

        A model must be a Python dict containing model attributes. See
        guild.guildfile.Guildfile for the expected structure.
        """
        return []

    def get_operation(self, _name, _modeldef, _config):
        """Return instance of OpDef for name, if supported for modeldef.

        Returns None if operation is not supported.
        """
        return None

    def enabled_for_op(self, _op):
        return False, None

    def run_op(self, op_spec, args):
        """The plugin should run the specified operation.

        Raises NotSupported if the plugin doesn't support the
        operation.
        """
        raise NotSupported(op_spec, args)

    def patch_env(self):
        pass

    def sync_run(self, _run, _options):
        raise TypeError("plugin '%s' does not support sync_run" % self.name)

    def stop_run(self, _run, _options):
        raise TypeError("plugin '%s' does not support stop_run" % self.name)

def iter_plugins():
    return iter(_plugins)

def for_name(name):
    return _plugins.one_for_name(name)

def limit_to_builtin():
    _plugins.set_path([__pkgdir__])
