# Copyright 2017 TensorHub, Inc.
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
import re

log = logging.getLogger("core")

class OpRefError(ValueError):
    pass

OpRef = collections.namedtuple(
    "OpRef", [
        "pkg_type",
        "pkg_name",
        "pkg_version",
        "model_name",
        "op_name"
    ])

def _opref_from_op(op_name, model_ref):
    (pkg_type,
     pkg_name,
     pkg_version,
     model_name) = model_ref
    return OpRef(pkg_type, pkg_name, pkg_version, model_name, op_name)

def _opref_from_run(run):
    opref_attr = run.get("opref")
    if not opref_attr:
        raise OpRefError(
            "run %s does not have attr 'opref')"
            % run.id)
    m = re.match(
        r"([^ :]+):([^ ]+) ([^ ]+) ([^ ]+) ([^ ]+)\s*$",
        opref_attr)
    if not m:
        raise OpRefError(
            "bad opref attr for run %s: %s"
            % (run.id, opref_attr))
    return OpRef(*m.groups())

def _opref_from_string(s):
    m = re.match(r"(?:(?:([^/]+)/)?([^:]+):)?([a-zA-Z0-9-_\.]+)(.*)$", s)
    if not m:
        raise OpRefError("invalid reference: %r" % s)
    pkg_name, model_name, op_name, extra = m.groups()
    return OpRef(None, pkg_name, None, model_name, op_name), extra

def _opref_is_op_run(opref, run):
    try:
        run_opref = _opref_from_run(run)
    except OpRefError as e:
        log.warning("unable to read opref for run %s: %s", run.id, e)
        return False
    else:
        return (
            run_opref.pkg_type == opref.pkg_type and
            run_opref.pkg_name == opref.pkg_name and
            run_opref.model_name == opref.model_name and
            run_opref.op_name == opref.op_name)

def _opref_to_string(opref):
    return "%s:%s %s %s %s" % (
        opref.pkg_type or "?",
        opref.pkg_name or "?",
        opref.pkg_version or "?",
        opref.model_name or "?",
        opref.op_name or "?")

OpRef.from_op = staticmethod(_opref_from_op)
OpRef.from_run = staticmethod(_opref_from_run)
OpRef.from_string = staticmethod(_opref_from_string)
OpRef.is_op_run = _opref_is_op_run
OpRef.__str__ = _opref_to_string
