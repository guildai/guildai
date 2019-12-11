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
import sys
import time

from guild import _api as gapi
from guild import exit_code
from guild import index2 as indexlib
from guild import op_util
from guild import run_util
from guild import util
from guild import var

from guild.commands import run_impl

log = logging.getLogger("guild")

DEFAULT_MAX_TRIALS = 20

class CurrentRunNotBatchError(Exception):
    pass

###################################################################
# Handle trials - run, print, save
###################################################################

def handle_trials(batch_run, trials):
    if os.getenv("PRINT_TRIALS_CMD") == "1":
        _print_trials_cmd(batch_run, trials)
    elif os.getenv("PRINT_TRIALS") == "1":
        _print_trials(trials)
    elif os.getenv("SAVE_TRIALS"):
        _save_trials(trials, os.getenv("SAVE_TRIALS"))
    else:
        _run_trials(batch_run, trials)

def _print_trials_cmd(batch_run, trials):
    for trial in trials:
        with util.TempDir() as tmp:
            run = _init_trial_run(batch_run, trial, tmp.path)
            run_impl.run(restart=run.dir, print_cmd=True)

def _print_trials(trials):
    if trials:
        op_util.print_trials(trials)

def _save_trials(trials, path):
    op_util.save_trials(trials, path)

def _run_trials(batch_run, trials):
    runs = _init_trial_runs(batch_run, trials)
    stage = os.getenv("STAGE_TRIALS") == "1"
    for run in runs:
        _start_trial_run(run, stage)

def _init_trial_runs(batch_run, trials):
    return [_init_trial_run(batch_run, trial) for trial in trials]

def _init_trial_run(batch_run, trial_flag_vals, run_dir=None):
    run = op_util.init_run(run_dir)
    _link_to_trial(batch_run, run)
    proto_run = batch_run.batch_proto
    util.copytree(proto_run.dir, run.dir)
    run.write_attr("flags", trial_flag_vals)
    run.write_attr("label", _trial_label(proto_run, trial_flag_vals))
    run.write_attr("op", _trial_op_attr(proto_run, trial_flag_vals))
    op_util.set_run_staged(run)
    return run

def _link_to_trial(batch_run, trial_run):
    trial_link = os.path.join(batch_run.dir, trial_run.id)
    rel_trial_path = os.path.relpath(trial_run.dir, os.path.dirname(trial_link))
    util.ensure_deleted(trial_link)
    os.symlink(rel_trial_path, trial_link)

def _trial_label(proto_run, trial_flag_vals):
    user_flag_vals = {
        name: val for name, val in trial_flag_vals.items()
        if val is not None
    }
    label_template = (proto_run.get("op") or {}).get("label_template")
    return op_util.run_label(label_template, user_flag_vals, trial_flag_vals)

def _start_trial_run(run, stage=False):
    _log_start_trial(run, stage)
    run_impl.run(restart=run.id, stage=stage)
    _maybe_trial_delay()

def _trial_op_attr(proto_run, trial_flag_vals):
    proto_op_data = proto_run.get("op")
    if not proto_op_data:
        return None
    deps = op_util.op_deps_for_data(proto_op_data.get("deps"))
    for dep in deps:
        dep.config = trial_flag_vals.get(dep.resdef.name) or dep.config
    proto_op_data["deps"] = op_util.op_deps_as_data(deps)
    return proto_op_data

def _log_start_trial(run, stage):
    log.info(
        "%s trial %s: %s (%s)",
        "Running" if not stage else "Staging",
        _trial_name(run),
        run_util.format_operation(run),
        _trial_flags_desc(run))

def _maybe_trial_delay():
    delay = os.getenv("TRIAL_DELAY")
    if delay:
        time.sleep(float(delay))

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

def run_trial(batch_run, flag_vals):
    run = _init_trial_run(batch_run, flag_vals)
    _start_trial_run(run)
    return run

###################################################################
# Utils
###################################################################

def is_batch(run):
    return os.path.exists(run.guild_path("proto"))

def batch_run():
    current_run = gapi.current_run()
    if not current_run:
        raise CurrentRunNotBatchError("no current run")
    proto_path = current_run.guild_path("proto")
    if not os.path.exists(proto_path):
        raise CurrentRunNotBatchError("missing proto %s" % proto_path)
    return current_run

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

def expanded_batch_trials(batch_run):
    proto_run = batch_run.batch_proto
    flag_vals = proto_run.get("flags") or {}
    trials = proto_run.get("trials")
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

def trial_results(batch_run, scalars):
    results = []
    runs = trial_runs(batch_run)
    index = _run_index_for_scalars(runs)
    for run in runs:
        results.append((
            run.get("flags"),
            _result_scalars(run, scalars, index)
        ))
    return results

def trial_runs(batch_run):
    runs = var.runs(batch_run.dir, sort=["timestamp"])
    # Update run dirs to real location rather than links under batch run.
    for run in runs:
        run.path = util.realpath(run.path)
    return runs

def _run_index_for_scalars(runs):
    index = indexlib.RunIndex()
    index.refresh(runs, ["scalar"])
    return index

def _result_scalars(run, scalars, index):
    return [_run_scalar(run, scalar, index) for scalar in scalars]

def _run_scalar(run, scalar, index):
    prefix, tag, qualifier = scalar
    return index.run_scalar(run, prefix, tag, qualifier, False)

def handle_system_exit(e):
    if isinstance(e.code, tuple) and len(e.code) == 2:
        msg, code = e.code
    elif isinstance(e.code, int):
        msg, code = None, e.code
    else:
        msg, code = e.message, exit_code.DEFAULT
    if msg:
        sys.stderr.write("guild: %s\n" % msg)
    sys.exit(code)
