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

import logging

from guild import guildfile
from guild import op_dep
from guild import plugin as pluginlib

log = logging.getLogger("guild")


class ResourceFlagsPlugin(pluginlib.Plugin):
    def guildfile_loaded(self, gf):
        for m in gf.models.values():
            for opdef in m.operations:
                apply_resource_flags(opdef)


def apply_resource_flags(opdef):
    for depdef in opdef.dependencies:
        resdef, _res_location = op_dep.resource_def(depdef, {})
        for source in resdef.sources:
            flagdef = _flagdef_for_source(source, opdef)
            if flagdef:
                _apply_flagdef(flagdef, opdef, source)


def _flagdef_for_source(source, opdef):
    flag_data = _flag_data_for_source(source)
    if not flag_data:
        return None
    return guildfile.FlagDef(flag_data["name"], flag_data, opdef)


def _flag_data_for_source(source):
    if source.parsed_uri.scheme == "file":
        return _flag_data_for_file(source)
    if source.parsed_uri.scheme == "operation":
        return _flag_data_for_operation(source)
    return None


def _flag_data_for_file(source):
    """Returns a flag def for a 'file' source.

    Because required files are generally not user-configurable
    (e.g. their content and paths are relied on by the operation) a
    flag is only generated when the source `flag-name` attribute is
    specified.

    For the same reason, `arg-skip` is true for generated flags to
    avoid passing required files as command arguments.

    The source `type` is `string` to avoid the side-effects of using
    `path` (e.g. convertion of the value to an absolute path).
    """
    assert source.parsed_uri.scheme == "file", source.parsed_uri
    if not source.flag_name:
        return None
    return {
        "name": source.flag_name,
        "arg-skip": True,
        "default": source.parsed_uri.path,
        "type": "string",
    }


def _apply_flagdef(flagdef, opdef, source):
    existing = opdef.get_flagdef(flagdef.name)
    if existing:
        _apply_missing_flagdef_attrs(flagdef, existing, opdef, source)
    else:
        opdef.flags.append(flagdef)


def _flag_data_for_operation(source):
    """Returns a flag def for an 'operation' source.

    Because required operations (runs) are often specified by users, a
    flag is generated unless `flag-name` is explicitly set to false in
    the source config.

    As with file source generated flags, `arg-skip` is true to avoid
    passing resolved run IDs as command arguments.

    """
    assert source.parsed_uri.scheme == "operation", source.parsed_uri
    if source.flag_name is False:
        return None
    name, alias = _operation_flag_name_and_alias_for_source(source)
    return {
        "name": name,
        "alias": alias,
        "arg-skip": True,
        "default": _operation_flag_default(),
        "type": "string",
    }


def _operation_flag_name_and_alias_for_source(source):
    """Returns a tuple of flag name and alias for an operation dependency.

    If `flag-name` is defined for `source` it is used with an alias of
    None. In this case the user has explicitly defined the interface
    and can provide an alias if need be.

    Similarly, if `name` is defined for `source` it is ued with an
    alias of None.

    If neither `flag-name` nor `name` is specified (the default case),
    the name is the source URI and the alias is the parsed URI
    path. This has the effect of showing the flag as
    `operation:<op-name>` in help text with support for the more
    convenient, shortened version of `<op-name>`.
    """
    if source.flag_name:
        return source.flag_name, None
    if source.name:
        return source.name, None
    return source.uri, source.parsed_uri.path


def _operation_flag_default():
    """Returns the default flag value for an operation source.

    This value is always None to ensure that Guild applies the default
    run resolution algorithm at run time.
    """
    return None


# List of flag attributes considered for merging (apply missing) from
# generated flag defs to user-defined (existing) flag defs. This list
# must be the set of all possible attributed generated for resource
# flags.
#
MERGE_FLAGDEF_ATTRS = ("arg_skip", "default")

# List of flag attributes that are always set even if a user has
# explicitly configured one. These values are forced because changing
# them could result in unintended/buggy behavior (e.g. setting the
# type of an operation flag to number, which coflicts with the
# required type of string for run IDs).
#
# Attributes are specified with corresponding source types (source URI
# scheme) and allowed values.
#
FORCE_FLAGDEF_ATTRS = (
    (
        "type",
        {
            "file": ("string", "path", "existing-path"),
            "operation": ("string",),
        },
    ),
)


def _apply_missing_flagdef_attrs(flagdef, existing, opdef, source):
    """Applies missing flag attributes in `flagdef` to `existing`.

    A missing attribute is an attribute with value None in `existing`.

    Only applies the attributes listed in `MERGE_FLAGDEF_ATTRS`. This
    list corresponds to the set of all possible flag attributes in
    generated flags.
    """
    _apply_merge_attrs(flagdef, existing)
    _apply_force_attrs(flagdef, existing, opdef, source)


def _apply_merge_attrs(flagdef, existing):
    for name in MERGE_FLAGDEF_ATTRS:
        existing_val = getattr(existing, name)
        if existing_val is None or name in FORCE_FLAGDEF_ATTRS:
            setattr(existing, name, getattr(flagdef, name))


def _apply_force_attrs(flagdef, existing, opdef, source):
    for name, source_allowed_vals in FORCE_FLAGDEF_ATTRS:
        allowed_vals = source_allowed_vals.get(source.parsed_uri.scheme)
        if not allowed_vals:
            continue
        existing_val = getattr(existing, name)
        if existing_val and existing_val not in allowed_vals:
            log.warning(
                "flag '%s' for operation %s is configured with %s '%s' - this "
                "value cannot be used because it conflicts with the "
                "dependency '%s' - ignoring configured value",
                flagdef.name,
                opdef.name,
                name,
                existing_val,
                source.resolving_name,
            )
            setattr(existing, name, getattr(flagdef, name))
