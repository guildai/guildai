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
import os

import six

from guild import cli
from guild import guildfile
from guild import util
from guild import yaml_util

log = logging.getLogger("guild")


class _ImportedFlagsOpDefProxy(object):
    def __init__(self, flags_data, wrapped_opdef):
        self.guildfile = wrapped_opdef.guildfile
        self.flags = self._init_flags(flags_data, wrapped_opdef.main)

    def _init_flags(self, flags_data, main_mod):
        flags = []
        for name, flag_data in flags_data.items():
            try:
                flag_data = guildfile.coerce_flag_data(name, flag_data, self.guildfile)
            except guildfile.GuildfileError as e:
                if os.getenv("NO_WARN_FLAGS_IMPORT") != "1":
                    log.warning("cannot import flags from %s: %s", main_mod, e)
            else:
                flags.append(guildfile.FlagDef(name, flag_data, self))
        return flags

    def flag_values(self):
        return {f.name: f.default for f in self.flags}


def apply_flags(opdef, import_flags_data_cb, apply_flags_data_cb=None):
    log_flags_info("### Script flags for %s", opdef.fullname)
    if _flags_import_disabled(opdef):
        log_flags_info("flags import disabled - skipping")
        return
    import_all_marker = object()
    to_import = _flags_to_import(opdef, import_all_marker)
    to_skip = _flags_to_skip(opdef)
    try:
        flags_data = import_flags_data_cb()
    except Exception as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception(repr(import_flags_data_cb))
        log.warning(e)
    else:
        if apply_flags_data_cb:
            apply_flags_data_cb(flags_data)
        import_data = {
            name: flags_data[name]
            for name in flags_data
            if (
                (to_import is import_all_marker or name in to_import)
                and not name in to_skip
            )
        }
        opdef.merge_flags(_ImportedFlagsOpDefProxy(import_data, opdef))


def log_flags_info(fmt, *args):
    if os.getenv("FLAGS_TEST") == "1":
        fmt_args = tuple([_fmt_arg(arg) for arg in args])
        cli.note(fmt % fmt_args)


def _fmt_arg(arg):
    if isinstance(arg, tuple):
        return arg[0](*arg[1:])
    return arg


def _flags_import_disabled(opdef):
    return opdef.flags_import in (False, [])


def _flags_to_import(opdef, all_marker):
    if opdef.flags_import in (True, "all"):
        return all_marker
    if opdef.flags_import is None:
        # If flags-import is not configured, import all defined flags.
        return set([flag.name for flag in opdef.flags])
    elif isinstance(opdef.flags_import, list):
        return set(opdef.flags_import)
    else:
        return set([opdef.flags_import])


def _flags_to_skip(opdef):
    if opdef.flags_import_skip:
        return set(opdef.flags_import_skip)
    return set()


def flag_data_for_val(val):
    return {
        "default": _flag_default(val),
        "type": _flag_type(val),
        "arg-split": _flag_arg_split(val),
    }


def _flag_default(val):
    if isinstance(val, list):
        return _encode_splittable_list(val)
    return val


def _encode_splittable_list(l):
    return " ".join([util.shlex_quote(yaml_util.encode_yaml(x)) for x in l])


def _flag_type(val):
    if isinstance(val, six.string_types):
        return "string"
    elif isinstance(val, bool):
        return "boolean"
    elif isinstance(val, (int, float)):
        return "number"
    else:
        return None


def _flag_arg_split(val):
    if isinstance(val, list):
        return True
    return None
