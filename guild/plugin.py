# Copyright 2017-2022 RStudio, PBC
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

import logging

from guild import __pkgdir__
from guild import entry_point_util

_plugins = entry_point_util.EntryPointResources("guild.plugins", "plugin")


class NotSupported(Exception):
    pass


class ModelOpResolutionError(Exception):
    pass


class Plugin:
    """Abstract interface for a Guild plugin."""

    name = None
    provides = []

    resolve_model_op_priority = 100
    sourcecode_select_rules_priority = 100

    def __init__(self, ep):
        self.name = ep.name
        self.log = logging.getLogger("guild." + self.name)

    def guildfile_data(self, data, src):
        """Called before data is used to initialize a Guildfile.

        Plugins may use this callback to mutate data before it's used.
        To modify a Guild file after it's been loaded, use
        `guildfile_loaded`.
        """

    def guildfile_loaded(self, gf):
        """Called immediately after a Guild file is loaded.

        Plugins may use this callback to modify a Guild file after
        it's been loaded. To modify the data before it's used to load
        the Guild file, use `guildfile_data`.
        """

    def enabled_for_op(self, opdef):
        # pylint: disable=unused-argument
        """Returns a tuple of boolean and reason.

        The boolean indicates whether or not the plugin is enabled for
        `opdef`. The reason is used to provide additional information to the
        user.
        """
        return False, "not applicable to operation"

    def patch_env(self):
        """Called to let the plugin patch the Python environment."""

    def resolve_model_op(self, opspec):
        # pylint: disable=unused-argument
        """Return a tuple of model, op_name for opspec.

        If opspec cannot be resolved to a model, the function should
        return None.
        """
        return None

    def resource_source_for_data(self, data, resdef):
        # pylint: disable=unused-argument
        """Return an instance of `guild.resourcedef.ResourceSource` for data.

        Return None if data is not supported as a resource source.
        """
        return None

    def resolver_class_for_source(self, source):
        # pylint: disable=unused-argument
        """Return a class (or factory) for a resolver suitable for `source`.

        `source` is an instance of `guild.resourcedef.ResourceSource`.

        Return None if resolution for the source is not supported by the plugin.
        """
        return None

    def run_staged(self, run, op):
        """Called when a run is staged.

        This called immediately before the run is marked as STAGED.

        The plugin must be enabled for the applicable run operation to be
        called.

        """

    def run_starting(self, run, op, pidfile):
        """Called when a run is starting.

        This called immediately before the run is marked as started.

        `pidfile` is provided when the run is started in the background. The
        plugin should poll the pidfile for creation and deletion to infer the
        run process start and end. `run_stopped()` is not called when a pidfile
        is provided.

        If `pidfile` is None, the operation is run in the foreground and
        `run_stopped()` is called, provided the parent process shuts down
        cleanly.
        """

    def run_stopped(self, run, op, exit_code):
        """Called when a run stops.

        `exit_code` is the numeric process exit code. 0 indicates that the
        process ended normally while a non-zero value indicates that an error
        occurred. The exit code is determined by the run process.

        This function is not called if the operation is started in the
        background (see `run_starting()` for details).
        """

    def apply_cmd_env(self, op, cmd_env):
        """Called in preparation of an operation command environment.

        Plugins should implement this to provide operation specific environment
        variables for use in a run.
        """

    def default_sourcecode_select_rules_for_op(self, opdef):
        # pylint: disable=unused-argument
        """Returns a default list of source code select rules for an operation.

        This is called only when the plugin is enabled for the operation and Guild.
        """
        return []


def iter_plugins():
    return iter(_plugins)


def for_name(name):
    return _plugins.one_for_name(name)


def limit_to_builtin():
    _plugins.set_path([__pkgdir__])
