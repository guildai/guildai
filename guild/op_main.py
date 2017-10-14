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

import imp
import logging
import os
import sys

import guild.log
import guild.plugin

def main():
    _init_logging()
    logging.debug("sys.path: %s", os.path.pathsep.join(sys.path))
    arg1, rest_args = _parse_args()
    _init_plugins()
    _apply_plugins()
    if arg1[0] == "@":
        _try_plugin(arg1[1:], rest_args)
    else:
        _try_module(arg1, rest_args)

def _init_logging():
    level = int(os.getenv("LOG_LEVEL", logging.WARN))
    format = os.getenv("LOG_FORMAT", "%(levelname)s: %(message)s")
    guild.log.init_logging(level, {"_": format})

def _parse_args():
    if len(sys.argv) < 2:
        _error("missing required arg\n")
    return sys.argv[1], sys.argv[2:]

def _init_plugins():
    guild.plugin.init_plugins()

def _apply_plugins():
    env = os.getenv("GUILD_PLUGINS")
    if env:
        for name in env.split(","):
            _apply_plugin(name)

def _apply_plugin(name):
    plugin = guild.plugin.for_name(name)
    plugin.patch_env()

def _try_plugin(plugin_op, args):
    plugin_name, op_spec = _parse_plugin_op(plugin_op)
    try:
        plugin = guild.plugin.for_name(plugin_name)
    except LookupError:
        _error("plugin '%s' not available" % plugin_name)
    else:
        _run_plugin_op(plugin, op_spec, args)

def _parse_plugin_op(plugin_op):
    parts = plugin_op.split(":", 1)
    if len(parts) == 1:
        _error("invalid plugin op: %s" % plugin_op)
    return parts

def _run_plugin_op(plugin, op_spec, args):
    try:
        plugin.op_for_spec(op_spec, args)
    except guild.plugin.NotSupported:
        _error(
            "plugin '%s' does not support operation '%s'"
            % (plugin.name, op_spec))
    except SystemExit as e:
        _handle_system_exit(e)

def _handle_system_exit(e):
    if isinstance(e.code, tuple) and len(e.code) == 2:
        msg, code = e.code
        sys.stderr.write(str(msg))
        sys.stderr.write("\n")
        sys.exit(code)
    elif isinstance(e.code, int):
        sys.exit(e.code)
    else:
        sys.stderr.write(str(e.message))
        sys.stderr.write("\n")
        sys.exit(1)

def _try_module(module_name, _args):
    logging.debug("finding module '%s'", module_name)
    try:
        module_info = imp.find_module(module_name)
    except ImportError as e:
        _error(str(e))
    else:
        _load_module_as_main(module_info)

def _load_module_as_main(module_info):
    f, path, desc = module_info
    logging.debug("loading module from '%s'", path)
    imp.load_module("__main__", f, path, desc)

def _error(msg):
    sys.stderr.write(msg)
    sys.stderr.write("\n")
    sys.exit(1)

if __name__ == "__main__":
    main()
