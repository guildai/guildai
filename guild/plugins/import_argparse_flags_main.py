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

# The odd naming convention below is to minimize the changes of
# colliding with symbols in the imported module.

import argparse as argparse
import json as json
import logging as logging
import os as os
import sys as sys

from guild import python_util as python_util

action_types = (
    argparse._StoreAction,
    argparse._StoreTrueAction,
    argparse._StoreFalseAction,
)


def _init_log():
    level = int(os.getenv("LOG_LEVEL", logging.WARN))
    format = os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    logging.basicConfig(level=level, format=format)
    return logging.getLogger("import_flags_main")


log = _init_log()


def main():
    args = _init_args()
    _patch_argparse(args.output_path)
    # Importing module has the side-effect of writing flag data due to
    # patched argparse.
    _exec_module(args.mod_path, args.package)


def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument("mod_path")
    p.add_argument("package")
    p.add_argument("output_path")
    return p.parse_args()


def _patch_argparse(output_path):
    handle_parse = lambda parse_args, *_args, **_kw: _write_flags(
        parse_args, output_path
    )
    # parse_known_args is called by parse_args, so this handles both
    # cases.
    python_util.listen_method(argparse.ArgumentParser, "parse_known_args", handle_parse)


def _write_flags(parse_args_f, output_path):
    parser = _wrapped_parser(parse_args_f)
    flags = {}
    for action in parser._actions:
        _maybe_apply_flag(action, flags)
    log.debug("writing flags to %s: %s", output_path, flags)
    with open(output_path, "w") as f:
        json.dump(flags, f)


def _wrapped_parser(f):
    return _closure_parser(_f_closure(f))


def _f_closure(f):
    try:
        return f.__closure__
    except AttributeError:
        try:
            return f.func_closure
        except AttributeError:
            assert False, (type(f), dir(f))


def _closure_parser(closure):
    assert isinstance(closure, tuple), (type(closure), closure)
    assert len(closure) == 2, closure
    parser = closure[1].cell_contents
    assert isinstance(parser, argparse.ArgumentParser), (type(parser), parser)
    return parser


def _maybe_apply_flag(action, flags):
    flag_name = _flag_name(action)
    if not flag_name:
        log.debug("skipping %s - not a flag option", action)
        return
    if not isinstance(action, action_types):
        log.debug("skipping %s - not an action type", action)
        return
    flags[flag_name] = attrs = {}
    if action.help:
        attrs["description"] = action.help
    if action.default is not None:
        attrs["default"] = _ensure_json_encodable(action.default, flag_name)
    if action.choices:
        attrs["choices"] = _ensure_json_encodable(action.choices, flag_name)
    if action.required:
        attrs["required"] = True
    if isinstance(action, argparse._StoreTrueAction):
        attrs["arg-switch"] = True
    elif isinstance(action, argparse._StoreFalseAction):
        attrs["arg-switch"] = False
    if _multi_arg(action):
        attrs["arg-split"] = True
    log.debug("added flag %r: %r", flag_name, attrs)


def _flag_name(action):
    for opt in action.option_strings:
        if opt.startswith("--"):
            return opt[2:]
    return None


def _ensure_json_encodable(x, flag_name):
    try:
        json.dumps(x)
    except TypeError:
        log.warning(
            "cannot serialize value %r for flag %s - coercing to string", x, flag_name
        )
        return str(x)
    else:
        return x


def _multi_arg(action):
    return action.nargs == "+" or (
        isinstance(action.nargs, (int, float)) and action.nargs > 1
    )


def _exec_module(mod_path, package):
    assert mod_path.endswith(".py"), mod_path
    sys.argv = [mod_path, "--help"]
    log.debug("loading module from '%s'", mod_path)
    python_util.exec_script(mod_path, mod_name=_exec_mod_name(package))


def _exec_mod_name(package):
    if package:
        return "%s.__main__" % package
    return "__main__"


if __name__ == "__main__":
    main()
