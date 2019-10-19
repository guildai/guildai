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
from guild import run_util
from guild import util
from guild import var

from guild.commands import run_impl2 as run_impl

log = logging.getLogger("guild")

class MissingProtoError(Exception):
    pass

###################################################################
# Stage / run trial
###################################################################

def stage_trial(proto_run, trial_flag_vals):
    run = op_util.init_run()
    util.copytree(proto_run.dir, run.dir)
    run.write_attr("flags", trial_flag_vals)
    run.write_attr("label", _trial_label(proto_run, trial_flag_vals))
    op_util.set_run_staged(run)
    return run

def _trial_label(proto_run, trial_flag_vals):
    user_flag_vals = {
        name: val for name, val in trial_flag_vals.items()
        if val is not None
    }
    label_template = (proto_run.get("op") or {}).get("label_template")
    return op_util.run_label(label_template, user_flag_vals, trial_flag_vals)

def start_staged_trial(run):
    _log_start_trial(run)
    run_impl.run(start=run.id)

def _log_start_trial(run):
    log.info(
        "Running trial %s: %s (%s)",
        _trial_name(run),
        run_util.format_operation(run),
        _trial_flags_desc(run))

def _trial_name(run):
    if util.compare_paths(os.path.dirname(run.dir), var.runs_dir()):
        return os.path.basename(run.dir)
    else:
        return "in %s" % run.dir

def _trial_flags_desc(run):
    flags = {
        name: val
        for name, val in (run.get("flags") or {}).items()
        if val is not None
    }
    return op_util.flags_desc(flags)

###################################################################
# Utils
###################################################################

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
        for name, val in sorted(flag_vals.items())
    ]
    return [dict(trial) for trial in itertools.product(*flag_list)]

def _trial_flags(flag_name, flag_val):
    if isinstance(flag_val, list):
        return [(flag_name, trial_val) for trial_val in flag_val]
    return [(flag_name, flag_val)]
