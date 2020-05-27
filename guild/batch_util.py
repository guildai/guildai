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

import csv
import itertools
import logging
import os
import random
import sys

from guild import _api as gapi
from guild import cli
from guild import exit_code
from guild import flag_util
from guild import op_util
from guild import run_util
from guild import util
from guild import var

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
    from guild.commands import run_impl

    for trial in trials:
        with util.TempDir() as tmp:
            run = _init_trial_run(batch_run, trial, tmp.path)
            run_impl.run(restart=run.dir, print_cmd=True)


def _print_trials(trials):
    if trials:
        data, cols = _trials_table_data(trials)
        cli.table(data, cols)


def _trials_table_data(trials):
    names = set()
    data = []
    for i, flags in enumerate(trials):
        row = {"_trial": i + 1}
        data.append(row)
        if flags:
            row.update({name: flag_util.encode_flag_val(flags[name]) for name in flags})
            names.update(flags)
    heading = {name: name for name in names}
    heading["_trial"] = "#"
    return [heading] + data, ["_trial"] + sorted(names)


def _save_trials(trials, path):
    data, cols = _trials_table_data(trials)
    cols.remove("_trial")  # Don't include trial number in CSV
    with open(path, "w") as f:
        out = csv.writer(f, lineterminator="\n")
        for row in data:
            out.writerow([row.get(name, "") for name in cols])


def _run_trials(batch_run, trials):
    trial_runs = _init_trial_runs(batch_run, trials)
    stage = batch_run.get("stage_trials")
    for trial_run in trial_runs:
        try:
            _start_trial_run(trial_run, stage)
        except SystemExit:
            _handle_trial_run_error(batch_run, trial_run)


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
    label_template = (proto_run.get("op") or {}).get("label_template")
    return op_util.run_label(label_template, trial_flag_vals)


def _start_trial_run(run, stage=False):
    from guild.commands import run_impl

    _log_start_trial(run, stage)
    run_impl.run(restart=run.id, stage=stage)


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
    desc = "Running" if not stage else "Staging"
    log.info(
        "%s trial %s: %s (%s)",
        desc,
        _trial_name(run),
        run_util.format_operation(run),
        _trial_flags_desc(run),
    )


def _trial_name(run):
    if util.compare_paths(os.path.dirname(run.dir), var.runs_dir()):
        return os.path.basename(run.dir)
    else:
        return "in %s" % run.dir


def _trial_flags_desc(run):
    flags = {
        name: val for name, val in (run.get("flags") or {}).items() if val is not None
    }
    return op_util.flags_desc(flags)


def _handle_trial_run_error(batch_run, trial_run):
    log.error(
        "trial %s exited with an error (see log for details)", _trial_name(trial_run)
    )
    if _fail_on_trial_error(batch_run):
        log.error(
            "stopping batch because a trial failed (remaining staged trials "
            "may be started as needed)"
        )
        raise SystemExit(exit_code.DEFAULT_ERROR)


def _fail_on_trial_error(batch_run):
    params = batch_run.get("run_params") or {}
    return params.get("fail_on_trial_error")


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
    flags_list = [_expand_flag(name, val) for name, val in sorted(flag_vals.items())]
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
    return trial_results_for_runs(trial_runs(batch_run), scalars)


def trial_results_for_runs(runs, scalars):
    index = _run_index_for_scalars(runs)
    return [(run.get("flags"), _result_scalars(run, scalars, index)) for run in runs]


def trial_runs(batch_run):
    runs = var.runs(batch_run.dir, sort=["timestamp"], force_root=True)
    # Update run dirs to real location rather than links under batch run.
    for run in runs:
        run.path = util.realpath(run.path)
    return runs


def _run_index_for_scalars(runs):
    from guild import index as indexlib  # expensive

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


def init_logging():
    op_util.init_logging()
