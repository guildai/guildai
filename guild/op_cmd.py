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

import logging
import pprint

import six

from guild import flag_util
from guild import util
from guild import yaml_util

log = logging.getLogger("guild")

###################################################################
# State
###################################################################


class OpCmd(object):
    def __init__(self, cmd_args, cmd_env, cmd_flags, flags_dest):
        self.cmd_args = cmd_args
        self.cmd_env = cmd_env
        self.cmd_flags = cmd_flags
        self.flags_dest = flags_dest


class CmdFlag(object):
    def __init__(
        self,
        arg_name=None,
        arg_skip=False,
        arg_switch=None,
        arg_split=None,
        env_name=None,
    ):
        self.arg_name = arg_name
        self.arg_skip = arg_skip
        self.arg_switch = arg_switch
        self.arg_split = arg_split
        self.env_name = env_name


###################################################################
# Generate command
###################################################################


def generate(op_cmd, flag_vals, resolve_params):
    return (_gen_args(op_cmd, flag_vals, resolve_params), _gen_env(op_cmd, flag_vals))


def _gen_args(op_cmd, flag_vals, resolve_params):
    encoded_resolve_params = _encode_arg_params(resolve_params)
    args = []
    for arg in op_cmd.cmd_args:
        if arg == "__flag_args__":
            args.extend(
                _flag_args(flag_vals, op_cmd.flags_dest, op_cmd.cmd_flags, args)
            )
        else:
            args.append(util.resolve_refs(arg, encoded_resolve_params))
    return args


def _encode_arg_params(params):
    return {name: _encode_general_arg(val) for name, val in params.items()}


def _encode_general_arg(val):
    # Use same encoding used for env vals.
    return _encode_env_val(val, arg_split=None)


def _flag_args(flag_vals, flag_dest, cmd_flags, cmd_args):
    args = []
    for name, val in sorted(flag_vals.items()):
        cmd_flag = cmd_flags.get(name)
        args.extend(_args_for_flag(name, val, cmd_flag, flag_dest, cmd_args))
    return args


def _args_for_flag(name, val, cmd_flag, flag_dest, cmd_args):
    cmd_flag = cmd_flag or CmdFlag()
    if cmd_flag.arg_skip:
        return []
    arg_name = cmd_flag.arg_name or name
    if "--%s" % arg_name in cmd_args:
        log.warning(
            "ignoring flag '%s=%s' because it's shadowed "
            "in the operation cmd as --%s",
            name,
            flag_util.encode_flag_val(val),
            arg_name,
        )
        return []
    elif cmd_flag.arg_switch is not None:
        if cmd_flag.arg_switch == val:
            return ["--%s" % arg_name]
        else:
            return []
    elif val is not None:
        if _splittable(val, cmd_flag):
            encoded = _encode_split_args(val, flag_dest, cmd_flag.arg_split)
            return ["--%s" % arg_name] + encoded if encoded else []
        else:
            return [
                "--%s" % arg_name,
                _encode_flag_arg(val, flag_dest, cmd_flag.arg_split),
            ]
    else:
        return []


def _splittable(val, cmd_flag):
    return not isinstance(val, list) and cmd_flag.arg_split is not None


def _encode_split_args(val, dest, arg_split):
    encoded = _encode_flag_val_for_split(val, dest, arg_split)
    parts = flag_util.split_encoded_flag_val(encoded, arg_split)
    return _split_args_for_dest(parts, dest)


def _encode_flag_val_for_split(val, dest, arg_split):
    if isinstance(val, six.string_types):
        return val
    return _encode_flag_arg(val, dest, arg_split)


def _split_args_for_dest(parts, dest):
    if dest == "globals":
        return [_encode_yaml_list_for_globals_arg(parts)]
    return parts


def _encode_yaml_list_for_globals_arg(parts):
    return yaml_util.encode_yaml(
        [yaml_util.decode_yaml(part) for part in parts],
        default_flow_style=True,
    )


def _encode_flag_arg(val, dest, arg_split):
    if dest == "globals" or dest.startswith("global:"):
        return _encode_flag_arg_for_globals(val)
    else:
        return _encode_flag_arg_for_argparse(val, arg_split)


def _encode_flag_arg_for_globals(val):
    """Returns an encoded flag value for Python globals interface.

    Flags destined for globals within a Python module are encoded
    using standard YAML encoding. Decoding must be handled using
    standard YAML decoding.
    """
    return yaml_util.encode_yaml(val, default_flow_style=True)


def _encode_flag_arg_for_argparse(val, arg_split):
    """Returns an encoded flag val for use by Python argparse.

    argparse generally uses type functions (e.g. int, float, etc.) to
    decode string args. We use `pprint.pformat` to encode here with
    exceptions for boolean values. Boolean values decode any non-empty
    string as True so we encode here accordingly using the arbitrarily
    chose non-empty string '1' to represent True along with the empty
    string '' to represent False.

    `arg_split` is used to encode lists of values to a single string
    argument.
    """
    if val is True:
        return "1"
    elif val is False or val is None:
        return ""
    elif isinstance(val, six.string_types):
        return val
    elif isinstance(val, list):
        return flag_util.join_splittable_flag_vals(val, arg_split)
    else:
        return pprint.pformat(val)


def _gen_env(op_cmd, flag_vals):
    env = _encoded_cmd_env(op_cmd)
    _resolve_env_flag_refs(flag_vals, env)
    _apply_flag_env(flag_vals, op_cmd, env)
    return env


def _encoded_cmd_env(op_cmd):
    return {name: _encode_env_val(val) for name, val in op_cmd.cmd_env.items()}


def _encode_env_val(val, arg_split=None):
    """Returns an encoded flag val for use as env values.

    Uses the same encoding scheme as _encode_flag_arg_for_argparse
    under the assumption that the same logic is used to decode env
    values as as command arguments.
    """
    return _encode_flag_arg_for_argparse(val, arg_split)


def _resolve_env_flag_refs(flag_vals, env):
    for env_name, env_val in env.items():
        env[env_name] = util.resolve_refs(env_val, flag_vals)


def _apply_flag_env(flag_vals, op_cmd, env):
    env.update(
        {
            _flag_env_name(name, op_cmd): _encode_env_val(val)
            for name, val in flag_vals.items()
        }
    )


def _flag_env_name(flag_name, op_cmd):
    cmd_flag = op_cmd.cmd_flags.get(flag_name)
    if cmd_flag and cmd_flag.env_name:
        return cmd_flag.env_name
    return _default_flag_env_name(flag_name)


def _default_flag_env_name(flag_name):
    return "FLAG_%s" % util.env_var_name(flag_name)


###################################################################
# Data IO
###################################################################


def for_data(data):
    cmd_args = data.get("cmd-args") or []
    cmd_env = data.get("cmd-env") or {}
    cmd_flags = _cmd_flags_for_data(data.get("cmd-flags"))
    flags_dest = data.get("flags-dest")
    return OpCmd(cmd_args, cmd_env, cmd_flags, flags_dest)


def _cmd_flags_for_data(data):
    if not data:
        return {}
    if not isinstance(data, dict):
        raise ValueError(data)
    return {
        flag_name: _cmd_flag_for_data(cmd_flag_data)
        for flag_name, cmd_flag_data in data.items()
    }


def _cmd_flag_for_data(data):
    if not isinstance(data, dict):
        raise ValueError(data)
    return CmdFlag(
        arg_name=data.get("arg-name"),
        arg_skip=data.get("arg-skip"),
        arg_switch=data.get("arg-switch"),
        arg_split=data.get("arg-split"),
        env_name=data.get("env-name"),
    )


def as_data(op_cmd):
    data = {
        "cmd-args": op_cmd.cmd_args,
    }
    if op_cmd.cmd_env:
        data["cmd-env"] = op_cmd.cmd_env
    cmd_flags_data = _cmd_flags_as_data(op_cmd.cmd_flags)
    if cmd_flags_data:
        data["cmd-flags"] = cmd_flags_data
    if op_cmd.flags_dest:
        data["flags-dest"] = op_cmd.flags_dest
    return data


def _cmd_flags_as_data(cmd_flags):
    data = {}
    for flag_name, cmd_flag in cmd_flags.items():
        cmd_flag_data = _cmd_flag_as_data(cmd_flag)
        if cmd_flag_data:
            data[flag_name] = cmd_flag_data
    return data


def _cmd_flag_as_data(cmd_flag):
    data = {}
    if cmd_flag.arg_name:
        data["arg-name"] = cmd_flag.arg_name
    if cmd_flag.arg_skip:
        data["arg-skip"] = cmd_flag.arg_skip
    if cmd_flag.arg_switch:
        data["arg-switch"] = cmd_flag.arg_switch
    if cmd_flag.arg_split is not None:
        data["arg-split"] = cmd_flag.arg_split
    if cmd_flag.env_name:
        data["env-name"] = cmd_flag.env_name
    return data
