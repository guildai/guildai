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

import collections
import logging
import os
import re

from guild import util

log = logging.getLogger("guild")


class OpRefError(ValueError):
    pass


OpRef = collections.namedtuple(
    "OpRef", ["pkg_type", "pkg_name", "pkg_version", "model_name", "op_name"]
)


def _opref_for_op(op_name, model_ref):
    (pkg_type, pkg_name, pkg_version, model_name) = model_ref
    return OpRef(pkg_type, pkg_name, pkg_version, model_name, op_name)


def _opref_parse(encoded):
    """Parses encoded opref.

    Format: PKG_TYPE_AND_NAME PKG_VER MODEL_NAME OP_NAME

    See _opref_for_string for parsing a user-provided value.
    """
    parts = util.shlex_split(encoded)
    if len(parts) != 4:
        raise OpRefError(encoded)
    pkg_type_and_name, pkg_ver, model_name, op_name = parts
    pkg_type, pkg_name = _split_pkg_type_and_name(pkg_type_and_name, encoded)
    return OpRef(pkg_type, pkg_name, pkg_ver, model_name, op_name)


def _split_pkg_type_and_name(s, encoded):
    parts = s.split(":", 1)
    if len(parts) != 2:
        raise OpRefError(encoded)
    return parts


def _opref_for_string(s):
    """Parses user-provided string to opref.

    See _opref_for_run for parsing a saved opref attr.
    """
    m = re.match(r"(?:(?:([^/]+)/)?([^:]+):)?([^/:]+)$", s)
    if not m:
        raise OpRefError("invalid reference: %r" % s)
    pkg_name, model_name, op_name = m.groups()
    return OpRef(None, pkg_name, None, model_name, op_name)


def _opref_is_op_run(opref, run, match_regex=False):
    try:
        run_opref = run.opref
    except OpRefError as e:
        log.warning("cannot read opref for run %s: %s", run.id, e)
        return False
    else:
        if not run_opref.op_name:
            log.warning("cannot get op name for run %s", run.id)
            return False
        return _cmp_oprefs(run_opref, opref, match_regex)


def _cmp_oprefs(run_opref, opref, match_regex):
    assert run_opref.op_name
    assert opref.op_name
    return (
        (opref.pkg_type is None or run_opref.pkg_type == opref.pkg_type)
        and (opref.pkg_name is None or run_opref.pkg_name == opref.pkg_name)
        and (opref.pkg_version is None or run_opref.pkg_version == opref.pkg_version)
        and (
            opref.model_name is None
            or _cmp(run_opref.model_name, opref.model_name, match_regex)
        )
        and _cmp(run_opref.op_name, opref.op_name, match_regex)
    )


def _cmp(val, compare_to, regex):
    log.debug("opref comparing %r to %r (regex=%r)", val, compare_to, regex)
    if not regex or compare_to == "+":
        return val == compare_to
    try:
        return re.match(r"%s$" % compare_to, val)
    except Exception as e:
        log.warning("error comparing %s using %s: %s", val, compare_to, e)
        return False


def _opref_to_string(opref):
    q = util.shlex_quote
    return "%s:%s %s %s %s" % (
        q(opref.pkg_type),
        q(opref.pkg_name),
        q(opref.pkg_version),
        q(opref.model_name),
        q(opref.op_name),
    )


def _maybe_quote(s):
    if s and re.search(r"\s", s):
        return "'{}'".format(s)
    return s


def _opref_lt(self, compare_to):
    return str(self) < str(compare_to)


def _opref_to_opspec(opref, cwd=None):
    spec_parts = []
    if opref.pkg_type == "script":
        return _script_path(opref, cwd)
    if opref.pkg_type == "package" and opref.pkg_name:
        spec_parts.extend([opref.pkg_name, "/"])
    if opref.model_name:
        spec_parts.extend([opref.model_name, ":"])
    if opref.op_name:
        spec_parts.append(opref.op_name)
    return "".join(spec_parts)


def _script_path(opref, cwd):
    path = os.path.join(opref.pkg_name, opref.op_name)
    if cwd:
        path = os.path.relpath(path, cwd)
    return path


OpRef.for_op = staticmethod(_opref_for_op)
OpRef.parse = staticmethod(_opref_parse)
OpRef.for_string = staticmethod(_opref_for_string)
OpRef.is_op_run = _opref_is_op_run
OpRef.__str__ = _opref_to_string
OpRef.__lt__ = _opref_lt
OpRef.to_opspec = _opref_to_opspec
