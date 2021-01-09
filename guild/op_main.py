# Copyright 2017-2020 TensorHub, Inc.
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

import warnings

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    import imp

import logging
import os
import pdb
import sys
import traceback

# Avoid expensive imports here as load times directly add to runs.

from guild import exit_code
from guild import op_util
from guild import util

log = None  # initialized in _init_logging

__argv0 = sys.argv

UNKNOWN_FLAGS_DEST = object()


class Debugger(pdb.Pdb):
    def __init__(self):
        pdb.Pdb.__init__(self)
        # Setting skip to True violates the Pdb interface, which
        # expected a list of globs, but we don't have such a list and
        # really just need a truthy value to trigger a call to
        # is_skipped_module, which implements the actual skip logic.
        self.skip = True

    def is_skipped_module(self, module_name):
        return module_name != "__main__"


class ModuleInfo(object):
    def __init__(self, mod_path, package):
        self.mod_path = mod_path
        self.package = package


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
        sys.stderr.write("Writing guild.op_main profile stats to %s\n" % tmp)
        p.dump_stats(tmp)
        sys.stderr.write(
            "Use 'python -m pstats %s' or 'snakeviz %s' to view stats\n" % (tmp, tmp)
        )


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
    op_util.init_logging()
    globals()["log"] = logging.getLogger("guild")


def _init_warnings():
    if log.getEffectiveLevel() > logging.DEBUG:
        warnings.simplefilter("ignore", Warning)
        warnings.filterwarnings("ignore", message="numpy.dtype size changed")
        warnings.filterwarnings("ignore", message="numpy.ufunc size changed")


def _parse_args():
    if len(sys.argv) < 2:
        _internal_error("missing required arg\n")
    return sys.argv[1], sys.argv[2:]


def _apply_plugins():
    plugins = os.getenv("GUILD_PLUGINS")
    if plugins:
        for name in plugins.split(","):
            _apply_plugin(name)


def _apply_plugin(name):
    plugin = _plugin_for_name(name)
    log.debug("patching env with plugin %r", name)
    plugin.patch_env()


def _plugin_for_name(name):
    from guild import plugin  # expensive

    return plugin.for_name(name)


def _try_module(arg1, args):
    module_spec = arg1.replace(os.path.sep, "/")
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
        _dispatch_module_exec(_flags_dest(args), module_info)


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
    """Find module using imp.find_module.

    While imp is deprecated, it provides a Python 2/3 compatible
    interface for finding a module. We use the result later to load
    the module with imp.load_module with the '__main__' name, causing
    it to execute.

    The non-deprecated method of using importlib.util.find_spec and
    loader.execute_module is not supported in Python 2.

    The _find_module implementation uses a novel approach to bypass
    imp.find_module's requirement that package directories contain
    __init__.py/__init__.pyc markers. This lets users specify
    namespace packages in main modules, which are not otherwise
    supported by imp.find_module.
    """
    parts = module.split(".")
    module_path = parts[0:-1]
    package = ".".join(module_path)
    module_name_part = parts[-1]
    # See function docstring for the rationale of this algorithm.
    for sys_path_item in sys.path:
        cur_path = os.path.join(sys_path_item, *module_path)
        try:
            f, path, _desc = imp.find_module(module_name_part, [cur_path])
        except ImportError:
            pass
        else:
            if f:
                f.close()
            else:
                path = _find_package_main(path)
                if path is None:
                    raise ImportError(
                        "No module named %s.__main__ ('%s' is a package "
                        "and cannot be directly executed)" % (module, module)
                    )
            return ModuleInfo(path, package)
    raise ImportError("No module named %s" % module)


def _find_package_main(mod_path):
    names = ["__main__.py", "__main__.pyc"]
    for name in names:
        path = os.path.join(mod_path, name)
        if os.path.exists(path):
            return path
    return None


def _flags_dest(args):
    dest = os.getenv("FLAGS_DEST", "args")
    if dest == "args" or dest.startswith("args:"):
        return _args_dest(args)
    elif dest == "globals":
        return _globals_dest(args)
    elif dest.startswith("global:"):
        return _global_dest(args, dest[7:])
    else:
        log.debug("guild.op_main ignoring flags dest %r", dest)
        return UNKNOWN_FLAGS_DEST, args, {}


def _args_dest(args):
    # Strip last occurring `--` from args
    flag_args, base_args = op_util.split_args_for_flags(args)
    return "args", base_args + flag_args, {}


def _globals_dest(args):
    base_args, flags = _base_args_and_flags_for_globals(args)
    return "globals", base_args, flags


def _base_args_and_flags_for_globals(args):
    flags, other_args = op_util.args_to_flags(args)
    return other_args, flags


def _global_dest(args, global_name):
    base_args, flags = _base_args_and_flags_for_globals(args)
    flags = util.nested_config(flags)
    global_dest = op_util.global_dest(global_name, flags)
    return "globals", base_args, global_dest


def _dispatch_module_exec(flags_interface, module_info):
    _maybe_test_internal_error()
    dest, args, flags = flags_interface
    if dest in ("args", UNKNOWN_FLAGS_DEST):
        _exec_module(module_info, args)
    elif dest == "globals":
        _exec_module(module_info, args, flags)
    else:
        assert False, flags_interface


def _maybe_test_internal_error():
    # Simulate an internal error by checking env for a special
    # variable. This is used by Guild tests to verify internal error
    # handling.
    assert os.getenv("__GUILD_OP_MAIN_INTERNAL_ERROR") != "1"


def _interrupt_handler():
    """Returns interrupt handler that's independent of module namespace."""
    if os.getenv("HANDLE_KEYBOARD_INTERRUPT"):
        return None
    # Save everything we need to handle interrupt.
    log_exception = log.getEffectiveLevel() <= logging.DEBUG
    log_exception_f = log.exception

    def handler():
        if log_exception:
            log_exception_f("interrupted")

    return handler


def _exec_module(module_info, args, globals=None):
    from guild import python_util

    _set_argv_for_module_with_args(module_info, args)

    def exec_script():
        mod_name = _module_name_for_info(module_info)
        log.debug("loading module from '%s'", module_info.mod_path)
        python_util.exec_script(module_info.mod_path, globals, mod_name=mod_name)

    _gen_exec(exec_script, module_info)


def _gen_exec(exec_cb, module_info):
    pdb_commands = _pdb_commands(module_info)
    if pdb_commands:
        debugger = Debugger()
        debugger.rcLines.extend(pdb_commands)
        debugger.runcall(exec_cb)
    else:
        # Use a closure to handle anything post load_module, which
        # effectively refefines the current module namespace.
        handle_interrupt = _interrupt_handler()
        try:
            exec_cb()
        except KeyboardInterrupt:
            if not handle_interrupt:
                raise
            handle_interrupt()


def _pdb_commands(module_info):
    try:
        encoded_breaks = os.environ["PDB_BREAKS"]
    except KeyError:
        return []
    else:
        unresolved_breaks = util.shlex_split(encoded_breaks)
        commands = [
            _pdb_break_cmd(_resolve_break(b, module_info)) for b in unresolved_breaks
        ]
        commands.append(_pdb_continue_cmd())
        return commands


def _pdb_break_cmd(location):
    # Include \n as Python 2.7 assumes line ending
    return "break %s\n" % location


def _pdb_continue_cmd():
    # Include \n as Python 2.7 assumes line ending
    return "continue\n"


def _resolve_break(b, module_info):
    import re

    if re.match(r"[0-9]+", b):
        return _module_break(module_info.mod_path, int(b))
    elif re.match(r".+?:[0-9]$", b):
        path, line = b.rsplit(":", 2)
        return _module_break(path, int(line), module_info.mod_path)
    else:
        return b


def _module_break(path, want_line, main_mod=None):
    from guild import python_util

    if not os.path.isabs(path):
        path = _resolve_path_for_break(path, main_mod)

    try:
        next_line = python_util.next_breakable_line(path, want_line)
    except TypeError:
        if want_line > 1:
            # Try first available breakpoint
            return _module_break(path, 1)
        else:
            return "%s:%i" % (path, want_line)
    else:
        return "%s:%i" % (path, next_line)


def _resolve_path_for_break(path, main_mod):
    debugger = pdb.Pdb()
    debugger.mainpyfile = main_mod or ''
    return debugger.lookupmodule(path)


def _set_argv_for_module_with_args(module_info, args):
    sys.argv = [module_info.mod_path] + args
    log.debug("argv: %s", sys.argv)


def _module_name_for_info(module_info):
    """Returns module name for module info.

    If module info contains a package, returns `<package.__main__`,
    otherwise returns `__main__`.
    """
    if module_info.package:
        return "%s.__main__" % module_info.package
    return "__main__"


def _internal_error(msg):
    sys.stderr.write("guild.op_main: %s\n" % msg)
    sys.exit(exit_code.INTERNAL_ERROR)


def _error(msg):
    sys.stderr.write("guild: %s\n" % msg)
    sys.exit(exit_code.DEFAULT_ERROR)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            raise
        exc_lines = traceback.format_exception(*sys.exc_info())
        if len(exc_lines) < 3 or len(__argv0) < 2:
            # Assertion failure, but we want to be defensive in
            # deference to the actual error.
            raise
        # Print exception start with mod (argv[0])
        filtered_exc_lines = []
        this_dir = os.path.dirname(__file__)
        for line in exc_lines[1:]:
            if filtered_exc_lines or this_dir not in line:
                filtered_exc_lines.append(line)
        if not filtered_exc_lines:
            raise
        sys.stderr.write(exc_lines[0])
        for line in filtered_exc_lines:
            sys.stderr.write(line)
        if os.getenv("BREAK_ON_ERROR") == "1":
            sys.stderr.write("Entering post mortem debug session\n")
            pdb.post_mortem()
        exit_code = e.code if isinstance(e, SystemExit) else 1
        sys.exit(exit_code)
