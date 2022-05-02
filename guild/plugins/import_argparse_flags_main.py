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

import argparse
import json
import logging
import sys

from guild import entry_point_util
from guild import flag_util
from guild import log as loglib
from guild import python_util
from guild import util


_action_importers = entry_point_util.EntryPointResources(
    "guild.python.argparse_actions", "Argparse action importers"
)


class ArgparseActionFlagsImporter(object):

    priority = 50

    def __init__(self, ep):
        self.ep = ep

    def flag_attrs_for_argparse_action(self, action, flag_name):
        """Return a dict of flag config attrs for an argparse action."""
        raise NotImplementedError()


flag_action_class_names = [
    "_StoreAction",
    "_StoreTrueAction",
    "_StoreFalseAction",
    "BooleanOptionalAction",
]

ignore_flag_action_class_names = [
    "_HelpAction",
]


loglib.init_logging()
log = logging.getLogger("guild.plugins.import_argparse_flags_main")


def main():
    args = _init_args()
    _patch_argparse(args.output_path)
    # Importing module has the side-effect of writing flag data due to
    # patched argparse.
    base_args = util.shlex_split(args.base_args)
    _exec_module(args.mod_path, args.package, base_args)


def _init_args():
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: import_argparse_flags_main.py "
            "mod_path package base_args output_path"
        )
    return argparse.Namespace(
        mod_path=sys.argv[1],
        package=sys.argv[2],
        base_args=sys.argv[3],
        output_path=sys.argv[4],
    )


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
        log.debug("skipping %s - not a flag action", action)
        return
    if action.__class__.__name__ not in flag_action_class_names:
        if action.__class__.__name__ not in ignore_flag_action_class_names:
            log.debug("skipping %s - not an action type", action)
        return
    attrs = _flag_attrs_for_action(action, flag_name)
    if attrs is not None:
        flags[flag_name] = attrs
        log.debug("added flag %r: %r", flag_name, attrs)
    else:
        log.debug("unable to import %s flag for action %r" % (flag_name, action))


def _flag_attrs_for_action(action, flag_name):
    for importer in _action_importers_by_priority():
        attrs = importer.flag_attrs_for_argparse_action(action, flag_name)
        if attrs is not None:
            return attrs
    return default_flag_attrs_for_argparse_action(action, flag_name)


def _action_importers_by_priority():
    importers = [importer for _name, importer in _action_importers]
    importers.sort(key=lambda x: x.priority)
    return importers


def default_flag_attrs_for_argparse_action(
    action, flag_name, ignore_unknown_type=False
):
    attrs = {}
    if action.help:
        attrs["description"] = action.help
    if action.default is not None:
        attrs["default"] = _ensure_json_encodable(action.default, flag_name)
    if action.choices:
        attrs["choices"] = _ensure_json_encodable(action.choices, flag_name)
    if action.required:
        attrs["required"] = True
    if action.type:
        attrs["type"] = _flag_type_for_action(
            action.type,
            flag_name,
            ignore_unknown_type,
        )
    if action.__class__.__name__ == "_StoreTrueAction":
        _apply_store_true_flag_attrs(attrs)
    elif action.__class__.__name__ == "_StoreFalseAction":
        _apply_store_false_flag_attrs(attrs)
    elif action.__class__.__name__ == "BooleanOptionalAction":
        _apply_boolean_option_flag_attrs(action, attrs)
    if _multi_arg(action):
        attrs["arg-split"] = True
        _maybe_encode_splittable_default(attrs)
    return attrs


def _ensure_json_encodable(x, flag_name):
    try:
        json.dumps(x)
    except TypeError:
        log.warning(
            "cannot serialize value %r for flag %s - coercing to string",
            x,
            flag_name,
        )
        return str(x)
    else:
        return x


def _flag_type_for_action(action_type, flag_name, ignore_unknown_type):
    if action_type is str:
        return "string"
    elif action_type is float:
        return "float"
    elif action_type is int:
        return "int"
    elif action_type is bool:
        return "boolean"
    else:
        if not ignore_unknown_type:
            log.warning(
                "unsupported flag type %s for flag %s - ignoring type setting",
                action_type,
                flag_name,
            )
        return None


def _apply_store_true_flag_attrs(attrs):
    attrs["arg-switch"] = True
    attrs["choices"] = [True, False]


def _apply_store_false_flag_attrs(attrs):
    attrs["arg-switch"] = False
    attrs["choices"] = [True, False]


def _apply_boolean_option_flag_attrs(action, attrs):
    if (
        len(action.option_strings) != 2
        or action.option_strings[0][:2] != "--"
        or action.option_strings[1][:2] != "--"
    ):
        log.debug(f"unexpected option_strings for action: {action}")
        return
    attrs["choices"] = [True, False]
    if action.default:
        attrs["arg-name"] = action.option_strings[1][2:]
        attrs["arg-switch"] = False
    else:
        attrs["arg-name"] = action.option_strings[0][2:]
        attrs["arg-switch"] = True


def _multi_arg(action):
    return action.nargs in ("+", "*") or (
        isinstance(action.nargs, (int, float)) and action.nargs > 1
    )


def _maybe_encode_splittable_default(flag_attrs):
    default = flag_attrs.get("default")
    if isinstance(default, list):
        flag_attrs["default"] = flag_util.join_splittable_flag_vals(default)


def _flag_name(action):
    for opt in action.option_strings:
        if opt.startswith("--"):
            return opt[2:]
    return None


def _exec_module(mod_path, package, base_args):
    assert mod_path.endswith(".py"), mod_path
    sys.argv = [mod_path] + base_args + ["--help"]
    log.debug("loading module from '%s'", mod_path)
    python_util.exec_script(mod_path, mod_name=_exec_mod_name(package))


def _exec_mod_name(package):
    if package:
        return "%s.__main__" % package
    return "__main__"


if __name__ == "__main__":
    main()
