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

import imp
import logging
import os
import pdb
import sys
import warnings

import guild.log

# Avoid expensive imports here as load times directly add to runs.

log = None # initialized in _init_logging

def main():
    if os.getenv("PROFILE"):
        _profile_main()
    else:
        _main()

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

def _main():
    _init_sys_path()
    _init_logging()
    _init_warnings()
    log.debug("cwd: %s", os.getcwd())
    log.debug("sys.path: %s", os.path.pathsep.join(sys.path))
    arg1, rest_args = _parse_args()
    _apply_plugins()
    _try_module(arg1, rest_args)

def _init_sys_path():
    if os.getenv("SCRIPT_DIR") is not None:
        sys.path[0] = os.getenv("SCRIPT_DIR")

def _init_logging():
    level = int(os.getenv("LOG_LEVEL", logging.WARN))
    format = os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    guild.log.init_logging(level, {"_": format})
    globals()["log"] = logging.getLogger("guild.op_main")

def _init_warnings():
    if log.getEffectiveLevel() > logging.DEBUG:
        warnings.simplefilter(action='ignore', category=FutureWarning)

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
    plugin = _plugin_for_name(name)
    plugin.patch_env()

def _plugin_for_name(name):
    from guild import plugin # expensive
    return plugin.for_name(name)

def _try_module(module_spec, args):
    package_path, module = _parse_module_spec(module_spec)
    if package_path:
        package_path = _try_resolve_package_path(package_path)
        log.debug("using package path '%s'", package_path)
        sys.path.insert(0, package_path)
    log.debug("finding module '%s'", module)
    try:
        module_info = _find_module(module)
    except ImportError as e:
        _error(str(e))
    else:
        _set_argv_for_module(module_info, args)
        _module_main(module_info)

def _parse_module_spec(spec):
    parts = spec.rsplit("/", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    else:
        return None, parts[0]

def _try_resolve_package_path(package_path):
    for path in sys.path:
        maybe_resolved = os.path.join(path, package_path)
        if os.path.exists(maybe_resolved):
            return maybe_resolved
    return package_path

def _find_module(module):
    parts = module.split(".")
    path = sys.path
    for part in parts:
        info = imp.find_module(part, path)
        path = [info[1]]
    return info

def _set_argv_for_module(module_info, args):
    _, path, _ = module_info
    sys.argv = [path] + args

def _module_main(module_info):
    f, path, desc = module_info
    log.debug("loading module from '%s'", path)
    if os.getenv("SET_TRACE"):
        debugger = Debugger()
        debugger.runcall(imp.load_module, "__main__", f, path, desc)
    else:
        try:
            imp.load_module("__main__", f, path, desc)
        except KeyboardInterrupt:
            if not os.getenv("HANDLE_KEYBOARD_INTERRUPT"):
                raise
            if log.getEffectiveLevel() <= logging.DEBUG:
                log.exception("KeyboardInterrupt")

class Debugger(pdb.Pdb):

    def __init__(self):
        pdb.Pdb.__init__(self)
        # Setting skip to True violates the Pdb interface, which is to
        # provide a list of globs, but we don't have such a list and
        # really just need a truthy value to trigger a call to
        # is_skipped_module, which implements the actual skip logic.
        self.skip = True

    def is_skipped_module(self, module_name):
        return module_name != "__main__"

def _error(msg):
    sys.stderr.write(msg)
    sys.stderr.write("\n")
    sys.exit(1)

if __name__ == "__main__":
    main()
