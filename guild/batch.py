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

import itertools
import logging
import os

from guild import _api as gapi
from guild import op2 as oplib
from guild import op_util2 as op_util
from guild import run as runlib
from guild import util
from guild import var

log = logging.getLogger("guild")

class MissingProtoError(Exception):
    pass

def proto_run():
    current_run = gapi.current_run()
    if not current_run:
        raise MissingProtoError("no current run")
    proto_path = current_run.guild_path("proto")
    if not os.path.exists(proto_path):
        raise MissingProtoError("missing proto %s" % proto_path)
    return runlib.Run("__proto__", proto_path)

def expand_flags(flag_vals):
    flag_list = [
        _trial_flags(name, val)
        for name, val in sorted(flag_vals.items())]
    return [dict(trial) for trial in itertools.product(*flag_list)]

def _trial_flags(flag_name, flag_val):
    if isinstance(flag_val, list):
        return [(flag_name, trial_val) for trial_val in flag_val]
    return [(flag_name, flag_val)]

def run_trial(proto_run, trial_flag_vals):
    proto_op = oplib.for_run(proto_run)
    opdef = _proto_opdef(proto_op)
    trial_op = _init_trial_op(proto_op, opdef, trial_flag_vals)
    _log_run_trial(trial_op)
    oplib.run(trial_op)

def _proto_opdef(proto_op):
    """Returns the opdef for a proto op.

    Batch runs require access to an operation definition because they
    generate new trials for a given set of flag values.
    """
    assert False, "NO"
    return op_util.opdef_for_opspec(proto_op.opref.to_opspec())

def _init_trial_op(proto_op, opdef, flag_vals):
    run = op_util.init_run()
    util.copytree(proto_op.run_dir, run.dir)
    return oplib.for_opdef(
        opdef,
        flag_vals,
        run_dir=run.dir,
    )

def _log_run_trial(op):
    log.info(
        "Running trial %s: %s (%s)",
        _op_trial_name(op),
        op.opref.to_opspec(),
        op_util.flags_desc(op.flag_vals))

def _op_trial_name(op):
    if util.compare_paths(os.path.dirname(op.run_dir), var.runs_dir()):
        return os.path.basename(op.run_dir)
    else:
        return "in %s" % op.run_dir
