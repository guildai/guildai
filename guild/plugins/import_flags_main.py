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

import argparse
import hashlib
import imp
import json
import logging
import os
import shutil
import sys

from guild import python_util
from guild import util
from guild import var

FLAGS = {}
MOD_INFO = None

action_types = (
    argparse._StoreAction,
    argparse._StoreTrueAction,
    argparse._StoreFalseAction,
)

def main():
    log = _init_log()
    args = _init_args()
    _patch_argparse(args.output)
    # Importing module has the side-effect of writing flag data due to
    # patched argparse
    _exec_module(args.module, args.output, log)

def _init_log():
    level = int(os.getenv("LOG_LEVEL", logging.WARN))
    format = os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    logging.basicConfig(level=level, format=format)
    return logging.getLogger("import_flags_main")

def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument("module")
    p.add_argument("output")
    return p.parse_args()

def _patch_argparse(output):
    python_util.listen_method(
        argparse.ArgumentParser,
        "add_argument",
        _handle_add_argument)
    python_util.listen_method(
        argparse.ArgumentParser,
        "parse_args",
        lambda *args, **kw: _write_flags_and_exit(output, *args, **kw))

def _handle_add_argument(add_argument, *args, **kw):
    action = add_argument(*args, **kw)
    _maybe_flag(action)
    raise python_util.Result(action)

def _maybe_flag(action):
    flag_name = _flag_name(action)
    if not flag_name:
        return
    if not isinstance(action, action_types):
        return
    FLAGS[flag_name] = attrs = {}
    if action.help:
        attrs["description"] = action.help
    if action.default is not None:
        attrs["default"] = action.default
    if action.choices:
        attrs["choices"] = action.choices
    if action.required:
        attrs["required"] = True
    if isinstance(action, argparse._StoreTrueAction):
        attrs["arg-switch"] = True
    elif isinstance(action, argparse._StoreFalseAction):
        attrs["arg-switch"] = False

def _flag_name(action):
    for opt in action.option_strings:
        if opt.startswith("--"):
            return opt[2:]
    return None

def _write_flags_and_exit(output, _parse_args, *_args, **_kw):
    with open(output, "w") as f:
        json.dump(FLAGS, f)
    _cache_data(output)

def _cache_data(output):
    assert MOD_INFO is not None
    _f, mod_path, _desc = MOD_INFO # pylint: disable=unpacking-non-sequence
    cached_data_path = _cached_data_path(mod_path)
    util.ensure_dir(os.path.dirname(cached_data_path))
    shutil.copyfile(output, cached_data_path)
    sys.exit(0)

def _cached_data_path(module_path):
    cache_dir = var.cache_dir("import-flags")
    abs_path = os.path.abspath(module_path)
    path_hash = hashlib.md5(abs_path.encode()).hexdigest()
    return os.path.join(cache_dir, path_hash)

def _exec_module(module, output, log):
    path, mod_name = _split_module(module)
    sys.path.insert(0, os.path.join(_guild_cwd(), path))
    try:
        module_info = _find_module(module)
    except ImportError as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("import {}".format(mod_name))
        sys.stderr.write("%s\n" % e)
        sys.exit(1)
    else:
        globals()["MOD_INFO"] = module_info
        _try_cached_data(module_info, output)
        _set_argv_for_module_help(module_info)
        _module_main(module_info, log)

def _guild_cwd():
    return os.getenv("GUILD_CWD") or "."

def _split_module(module):
    parts = module.rsplit("/", 1)
    if len(parts) == 1:
        return ".", parts[0]
    return parts

def _find_module(module):
    # Copied from guild.op_main
    parts = module.split(".")
    module_path = parts[0:-1]
    module_name_part = parts[-1]
    for sys_path_item in sys.path:
        cur_path = os.path.join(sys_path_item, *module_path)
        try:
            return imp.find_module(module_name_part, [cur_path])
        except ImportError:
            pass
    raise ImportError("No module named %s" % module)

def _try_cached_data(module_info, output):
    _f, module_path, _desc = module_info
    cached_data_path = _cached_data_path(module_path)
    if _cache_valid(cached_data_path, module_path):
        shutil.copyfile(cached_data_path, output)
        sys.exit(0)

def _cache_valid(cache, marker):
    if not os.path.exists(cache):
        return False
    return os.path.getmtime(marker) <= os.path.getmtime(cache)

def _set_argv_for_module_help(module_info):
    _, path, _ = module_info
    sys.argv = [path, "--help"]

def _module_main(module_info, log):
    f, path, desc = module_info
    log.debug("loading module from '%s'", path)
    imp.load_module("__main__", f, path, desc)

if __name__ == "__main__":
    main()
