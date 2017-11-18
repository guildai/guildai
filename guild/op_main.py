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

# Avoid expensive imports here as load times directly add to runs.

log = None # initialized in _init_logging

def main():
    if os.getenv("PROFILE"):
        _profile_main()
    else:
        _main()

def _main():
    _init_sys_path()
    _init_logging()
    log.debug("cwd: %s", os.getcwd())
    log.debug("sys.path: %s", os.path.pathsep.join(sys.path))
    arg1, rest_args = _parse_args()
    _apply_plugins()
    if arg1[0] == "@":
        _try_plugin(arg1[1:], rest_args)
    else:
        _try_module(arg1, rest_args)

def _init_sys_path():
    if os.getenv("SCRIPT_DIR") is not None:
        sys.path[0] = os.getenv("SCRIPT_DIR")

def _init_logging():
    level = int(os.getenv("LOG_LEVEL", logging.WARN))
    format = os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    guild.log.init_logging(level, {"_": format})
    globals()["log"] = logging.getLogger("guild.op_main")

def _parse_args():
    if len(sys.argv) < 2:
        _error("missing required arg\n")
    return sys.argv[1], sys.argv[2:]

def _apply_plugins():
    env = os.getenv("GUILD_PLUGINS")
    if env:
        for name in env.split(","):
            _apply_plugin(name)

def _apply_plugin(name):
    import guild.plugin
    plugin = _plugin_for_name(name)
    plugin.patch_env()

def _plugin_for_name(name):
    from guild import plugin # expensive
    return plugin.for_name(name)

def _try_plugin(plugin_op, args):
    plugin_name, op_spec = _parse_plugin_op(plugin_op)
    try:
        plugin = _plugin_for_name(plugin_name)
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
    log.debug("running plugin op '@%s:%s' %r", plugin.name, op_spec, args)
    try:
        plugin.run_op(op_spec, args)
    except Exception as e:
        from guild.plugin import NotSupported # expensive
        if isinstance(e, NotSupported):
            _error(
                "plugin '%s' does not support operation '%s'"
                % (plugin.name, op_spec))
        raise
    except SystemExit as e:
        _handle_system_exit(e)

def _handle_system_exit(e):
    if isinstance(e.code, tuple) and len(e.code) == 2:
        msg, code = e.code
        sys.stderr.write("guild: ")
        sys.stderr.write(str(msg))
        sys.stderr.write("\n")
        sys.exit(code)
    elif isinstance(e.code, int):
        sys.exit(e.code)
    else:
        sys.stderr.write("guild: ")
        sys.stderr.write(str(e.message))
        sys.stderr.write("\n")
        sys.exit(1)

def _try_module(module_spec, args):
    package_path, module_path = _parse_module_spec(module_spec)
    if package_path:
        log.debug("using package path '%s'", package_path)
        sys.path.insert(0, package_path)
    log.debug("finding module '%s'", module_path)
    try:
        module_info = imp.find_module(module_path)
    except ImportError as e:
        _error(str(e))
    else:
        _set_argv_for_module(module_info, args)
        _module_main(module_info)

def _parse_module_spec(spec):
    parts = spec.rsplit("/", 1)
    if len(parts) == 2:
        return parts[0], parts[1].replace(".", os.path.sep)
    else:
        return None, parts[0].replace(".", os.path.sep)

def _set_argv_for_module(module_info, args):
    _, path, _ = module_info
    sys.argv = [path] + args

def _module_main(module_info):
    f, path, desc = module_info
    log.debug("loading module from '%s'", path)
    imp.load_module("__main__", f, path, desc)

def _error(msg):
    sys.stderr.write(msg)
    sys.stderr.write("\n")
    sys.exit(1)

def _profile_main():
    import cProfile
    import tempfile
    p = cProfile.Profile()
    sys.stderr.write("Profiling operation\n")
    p.enable()
    try:
        _main()
    finally:
        p.disable()
        _, tmp = tempfile.mkstemp(prefix="guild-op-profile-")
        sys.stderr.write("Writing profile stats to %s\n" % tmp)
        p.dump_stats(tmp)
        sys.stderr.write(
            "Use 'python -m pstats %s' or 'snakeviz %s' "
            "to view stats\n" % (tmp, tmp))
