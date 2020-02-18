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

import warnings as ___warnings

with ___warnings.catch_warnings():
    ___warnings.filterwarnings('ignore', category=DeprecationWarning)
    import imp as ___imp

import argparse as ___argparse
import json as ___json
import logging as ___logging
import os as ___os
import sys as ___sys

from guild import python_util as ___python_util

___P_FLAGS = {}

___action_types = (
    ___argparse._StoreAction,
    ___argparse._StoreTrueAction,
    ___argparse._StoreFalseAction,
)


def ___init_log():
    level = int(___os.getenv("LOG_LEVEL", ___logging.WARN))
    format = ___os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    ___logging.basicConfig(level=level, format=format)
    return ___logging.getLogger("import_flags_main")


___log = ___init_log()


def ___main():
    args = ___init_args()
    ___patch_argparse(args.output_path)
    # Importing module has the side-effect of writing flag data due to
    # patched argparse.
    ___exec_module(args.mod_path)


def ___init_args():
    p = ___argparse.ArgumentParser()
    p.add_argument("mod_path")
    p.add_argument("output_path")
    return p.parse_args()


def ___patch_argparse(output_path):
    ___python_util.listen_method(
        ___argparse.ArgumentParser, "add_argument", ___handle_add_argument
    )
    ___handle_parse = lambda parse_args, *_args, **_kw: ___write_flags_and_exit(
        parse_args, output_path
    )
    # parse_known_args is called by parse_args, so this handled both
    # cases.
    ___python_util.listen_method(
        ___argparse.ArgumentParser, "parse_known_args", ___handle_parse
    )


def ___handle_add_argument(add_argument_f, *args, **kw):
    ___log.debug("handling add_argument: %s %s", args, kw)
    parser = ___wrapped_parser(add_argument_f)
    action = add_argument_f(*args, **kw)
    ___maybe_flag(parser, action)
    raise ___python_util.Result(action)


def ___wrapped_parser(f):
    return ___closure_parser(___f_closure(f))


def ___f_closure(f):
    try:
        return f.__closure__
    except AttributeError:
        try:
            return f.func_closure
        except AttributeError:
            assert False, (type(f), dir(f))


def ___closure_parser(closure):
    assert isinstance(closure, tuple), (type(closure), closure)
    assert len(closure) == 2, closure
    parser = closure[1].cell_contents
    assert isinstance(parser, ___argparse.ArgumentParser), (type(parser), parser)
    return parser


def ___maybe_flag(parser, action):
    flag_name = ___flag_name(action)
    if not flag_name:
        ___log.debug("skipping %s - not a flag option", action)
        return
    if not isinstance(action, ___action_types):
        ___log.debug("skipping %s - not an action type", action)
        return
    flags = ___P_FLAGS.setdefault(parser, {})
    flags[flag_name] = attrs = {}
    if action.help:
        attrs["description"] = action.help
    if action.default is not None:
        attrs["default"] = ___ensure_json_encodable(action.default, flag_name)
    if action.choices:
        attrs["choices"] = ___ensure_json_encodable(action.choices, flag_name)
    if action.required:
        attrs["required"] = True
    if isinstance(action, ___argparse._StoreTrueAction):
        attrs["arg-switch"] = True
    elif isinstance(action, ___argparse._StoreFalseAction):
        attrs["arg-switch"] = False
    ___log.debug("added flag %s", attrs)


def ___flag_name(action):
    for opt in action.option_strings:
        if opt.startswith("--"):
            return opt[2:]
    return None


def ___ensure_json_encodable(x, flag_name):
    try:
        ___json.dumps(x)
    except TypeError:
        ___log.warning(
            "cannot serialize value %r for flag %s - coercing to string", x, flag_name
        )
        return str(x)
    else:
        return x


def ___write_flags_and_exit(parse_args_f, output_path):
    parser = ___wrapped_parser(parse_args_f)
    flags = ___P_FLAGS.get(parser, {})
    assert isinstance(flags, dict), flags
    ___log.debug("writing flags to %s: %s", output_path, flags)
    with open(output_path, "w") as f:
        ___json.dump(flags, f)


def ___exec_module(mod_path):
    assert mod_path.endswith(".py")
    f = open(mod_path, "r")
    details = (".py", "r", 1)
    ___sys.argv = [mod_path, "--help"]
    ___log.debug("loading module from '%s'", mod_path)
    ___imp.load_module("__main__", f, mod_path, details)


if __name__ == "__main__":
    ___main()
