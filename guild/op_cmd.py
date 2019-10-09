# Copyright 2017-2019 TensorHub, Inc.
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

from guild import flag_util
from guild import util

###################################################################
# State
###################################################################

class CmdTemplate(object):

    def __init__(self, cmd_args, flag_args):
        self.cmd_args = cmd_args
        self.flag_args = flag_args

class FlagArg(object):

    def __init__(self, arg_name=None, arg_skip=False, arg_switch=None):
        self.arg_name = arg_name
        self.arg_skip = arg_skip
        self.arg_switch = arg_switch

###################################################################
# Generate command
###################################################################

def cmd_args(template, flag_vals):
    args = []
    for arg in template.cmd_args:
        if arg == "__flag_args__":
            args.extend(_flag_args(template.flag_args, flag_vals))
        else:
            args.append(arg)
    return args

def _flag_args(arg_specs, flag_vals):
    args = []
    for name, val in sorted(flag_vals.items()):
        args.extend(_args_for_flag(name, val, arg_specs.get(name)))
    return args

def _args_for_flag(name, val, arg_spec):
    arg_spec = arg_spec or FlagArg()
    if arg_spec.arg_skip:
        return []
    arg_name = arg_spec.arg_name or name
    if arg_spec.arg_switch is not None:
        if arg_spec.arg_switch == val:
            return ["--%s" % arg_name]
        else:
            return []
    elif val is not None:
        return ["--%s" % arg_name, flag_util.encode_flag_val(val)]
    else:
        return []

###################################################################
# Data IO
###################################################################

def for_data(data):
    cmd_args = data.get("cmd-args") or []
    flag_args = _flag_args_for_data(data.get("flag-args"))
    return CmdTemplate(cmd_args, flag_args)

def _flag_args_for_data(data):
    if not data:
        return {}
    if not isinstance(data, dict):
        raise ValueError(data)
    return {
        flag_name: _flag_arg_for_data(flag_arg_data)
        for flag_name, flag_arg_data in data.items()
    }

def _flag_arg_for_data(data):
    if not isinstance(data, dict):
        raise ValueError(data)
    return FlagArg(
        arg_name=data.get("arg-name"),
        arg_skip=data.get("arg-skip"),
        arg_switch=data.get("arg-switch"),
    )

def as_data(cmd_template):
    data = {
        "cmd-args": cmd_template.cmd_args,
    }
    flag_args_data = _flag_args_as_data(cmd_template.flag_args)
    if flag_args_data:
        data["flag-args"] = flag_args_data
    return data

def _flag_args_as_data(flag_args):
    data = {}
    for flag_name, flag_arg in flag_args.items():
        flag_arg_data = _flag_arg_as_data(flag_arg)
        if flag_arg_data:
            data[flag_name] = flag_arg_data
    return data

def _flag_arg_as_data(flag_arg):
    data = {}
    if flag_arg.arg_name:
        data["arg-name"] = flag_arg.arg_name
    if flag_arg.arg_skip:
        data["arg-skip"] = flag_arg.arg_skip
    if flag_arg.arg_switch:
        data["arg-switch"] = flag_arg.arg_switch
    return data
