# Copyright 2017-2019 TensorHub, Inc.
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

class NotSupported(Exception):
    pass

class Plugin(object):
    """Abstract interface for a Guild plugin."""

    name = None

    resolve_model_op_priority = 100

    def __init__(self, ep):
        self.name = ep.name
        self.log = logging.getLogger("guild." + self.name)

    def guildfile_data(self, _data, _src):
        """Called before data is used to initialize a Guildfile.

        Plugins may use this callback to mutate data before it's used.
        To modify a Guild file after it's been loaded, use
        `guildfile_loaded`.
        """
        pass

    def guildfile_loaded(self, _gf):
        """Called immediately after a Guild file is loaded.

        Plugins may use this callback to modify a Guild file after
        it's been loaded. To modify the data before it's used to load
        the Guild file, use `guildfile_data`.
        """
        pass

    @staticmethod
    def enabled_for_op(_op):
        return False, None

    @staticmethod
    def patch_env():
        pass

    @staticmethod
    def resolve_model_op(_opspec):
        """Return a tuple of model, op_name for opspec.

        If opspec cannot be resolved to a model, the function should
        return None.
        """
        return None

def iter_plugins():
    return iter(_plugins)

def for_name(name):
    return _plugins.one_for_name(name)

def limit_to_builtin():
    _plugins.set_path([__pkgdir__])
