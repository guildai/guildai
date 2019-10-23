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
import random

from guild import _api as gapi
from guild import op2 as oplib
from guild import op_util2 as op_util
from guild import run as runlib
from guild import run_util
from guild import util
from guild import var

from guild.commands import run_impl2 as run_impl

log = logging.getLogger("guild")

DEFAULT_MAX_TRIALS = 20

class CurrentRunNotBatchError(Exception):
    pass

###################################################################
# Handle trials
###################################################################

def handle_trials(proto_run, trials):
    if os.getenv("PRINT_TRIALS_CMD") == "1":
        _print_trials_cmd(proto_run, trials)
    elif os.getenv("PRINT_TRIALS") == "1":
        _print_trials(trials)
    elif os.getenv("SAVE_TRIALS"):
        _save_trials(trials, os.getenv("SAVE_TRIALS"))
    else:
        _run_trials(proto_run, trials)

def _print_trials_cmd(proto_run, trials):
    for trial in trials:
        with util.TempDir() as tmp:
            run = _init_trial_run(proto_run, trial, tmp.path)
            run_impl.run(start=run.dir, print_cmd=True)

def _print_trials(trials):
    if trials:
        op_util.print_trials(trials)

def _save_trials(trials, path):
    op_util.save_trials(trials, path)

def _run_trials(proto_run, trials):
    runs = _init_trial_runs(proto_run, trials)
    stage = os.getenv("STAGE_TRIALS") == "1"
    for run in runs:
        _start_trial_run(run, stage)

def _init_trial_runs(proto_run, trials):
    return [_init_trial_run(proto_run, trial) for trial in trials]

def _init_trial_run(proto_run, trial_flag_vals, run_dir=None):
    run = op_util.init_run(run_dir)
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

def _start_trial_run(run, stage):
    _log_start_trial(run, stage)
    run_impl.run(start=run.id, stage=stage)

def _log_start_trial(run, stage):
    log.info(
        "%s trial %s: %s (%s)",
        "Running" if not stage else "Staging",
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

def batch_run():
    current_run = gapi.current_run()
    if not current_run:
        raise CurrentRunNotBatchError("no current run")
    proto_path = current_run.guild_path("proto")
    if not os.path.exists(proto_path):
        raise CurrentRunNotBatchError("missing proto %s" % proto_path)
    return current_run

def proto_run():
    proto_path = batch_run().guild_path("proto")
    assert os.path.exists(proto_path)
    return runlib.Run("__proto__", proto_path)

def expand_flags(flag_vals):
    flags_list = [
        _expand_flag(name, val)
        for name, val in sorted(flag_vals.items())
    ]
    return [dict(flags) for flags in itertools.product(*flags_list)]

def _expand_flag(name, val):
    if isinstance(val, list):
        return [(name, x) for x in val]
    return [(name, val)]

def batch_trials_for_proto_run(run=None):
    run = run or proto_run()
    flag_vals = run.get("flags") or {}
    trials = run.get("trials")
    if trials:
        return expand_flags_with_trials(flag_vals, trials)
    return expand_flags(flag_vals)

def expand_flags_with_trials(flag_vals, trials):
    expanded = []
    for trial_flag_vals in trials:
        merged_flags = _merged_trial_flags(trial_flag_vals, flag_vals)
        expanded.extend(expand_flags(merged_flags))
    return expanded

def _merged_trial_flags(trial_flag_vals, flag_vals):
    merged = dict(flag_vals)
    merged.update(trial_flag_vals)
    return merged

def sample_trials(trials, count=None, random_seed=None):
    count = count or DEFAULT_MAX_TRIALS
    if len(trials) <= count:
        return trials
    random.seed(random_seed)
    # Sample indices and re-sort to preserve original trial order.
    sampled_i = random.sample(range(len(trials)), count)
    return [trials[i] for i in sorted(sampled_i)]
