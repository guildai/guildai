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
import json
import itertools
import logging
import os
import random
import sys

import six

from guild import _api as gapi
from guild import cli
from guild import exit_code
from guild import flag_util
from guild import lock as locklib
from guild import op_util
from guild import run_util
from guild import util
from guild import var

log = logging.getLogger("guild")

DEFAULT_MAX_TRIALS = 20
DEFAULT_OBJECTIVE = "loss"

RUN_STATUS_LOCK_TIMEOUT = 30


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
            run = init_trial_run(batch_run, trial, tmp.path)
            run_impl.run(restart=run.dir, print_cmd=True)


def _print_trials(trials):
    if trials:
        data, cols = _trials_table_data(trials, format=True)
        cli.table(data, cols)


def _trials_table_data(trials, format=False):
    names = set()
    data = []
    maybe_format = flag_util.encode_flag_val if format else lambda x: x
    for i, flags in enumerate(trials):
        row = {"_trial": i + 1}
        data.append(row)
        if flags:
            row.update({name: maybe_format(flags[name]) for name in flags})
            names.update(flags)
    heading = {name: name for name in names}
    heading["_trial"] = "#"
    return [heading] + data, ["_trial"] + sorted(names)


def _save_trials(trials, path):
    _, ext = os.path.splitext(path)
    if ext.lower() == ".json":
        _save_trials_json(trials, path)
    else:
        assert ext.lower() in (".csv", ""), "unsupported extension in path '%s'" % path
        _save_trials_csv(trials, path)


def _save_trials_json(trials, path):
    data, _ = _trials_table_data(trials, format=False)
    with open(path, "w") as f:
        json.dump(_strip_trial_nums(data[1:]), f, sort_keys=True)


def _strip_trial_nums(data):
    return [{name: row[name] for name in row if name != "_trial"} for row in data]


def _save_trials_csv(trials, path):
    data, cols = _trials_table_data(trials, format=True)
    with open(path, "w") as f:
        out = csv.writer(f, lineterminator="\n")
        for row in data:
            row_vals = [row.get(name, "") for name in cols if name != "_trial"]
            out.writerow(row_vals)


def _run_trials(batch_run, trials):
    trial_runs = _init_trial_runs(batch_run, trials)
    run_status_lock = locklib.Lock(locklib.RUN_STATUS, timeout=RUN_STATUS_LOCK_TIMEOUT)
    for trial_run in trial_runs:
        _try_run_staged_trial(trial_run, batch_run, run_status_lock)


def _init_trial_runs(batch_run, trials):
    return [init_trial_run(batch_run, trial) for trial in trials]


def init_trial_run(batch_run, trial_flag_vals, run_dir=None):
    run = op_util.init_run(run_dir)
    _link_to_trial(batch_run, run)
    proto_run = batch_run.batch_proto
    assert proto_run, "proto_run not initialized for batch %s (%s)" % (
        batch_run.id,
        batch_run.dir,
    )
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


def _try_run_staged_trial(trial_run, batch_run, status_lock):
    stage = batch_run.get("stage_trials")
    with status_lock:
        trial_status = trial_run.status
        if trial_status != "staged":
            log.warning(
                "Skipping %s - status is '%s' but expected 'staged'",
                trial_run.id,
                trial_status,
            )
            return
    # Race condition here. Correct implementation is to pass the
    # lock through and release after trial_run status is changed.
    try:
        start_trial_run(trial_run, stage)
    except SystemExit as e:
        _handle_trial_run_error(e, batch_run, trial_run)


def start_trial_run(run, stage=False):
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


def _handle_trial_run_error(e, batch_run, trial_run):
    is_error = log_trial_run_error(e, trial_run)
    if is_error and fail_on_trial_error(batch_run):
        log.error(
            "Stopping batch because a trial failed (remaining staged trials "
            "may be started as needed)"
        )
        raise SystemExit(exit_code.DEFAULT_ERROR)


def log_trial_run_error(e, trial_run):
    from guild import main

    msg, code = main.system_exit_params(e)
    if code == 0:
        if msg:
            log.info(msg)
        return False
    log.error(
        "Trial %s exited with an error%s",
        _trial_name(trial_run),
        _trial_run_error_desc(code, msg),
    )
    return True


def _trial_run_error_desc(code, msg):
    if msg:
        return ": (%i) %s" % (code, msg)
    else:
        return " (%i) - see log for details" % code


def fail_on_trial_error(batch_run):
    params = batch_run.get("run_params") or {}
    return params.get("fail_on_trial_error")


def run_trial(batch_run, flag_vals):
    run = init_trial_run(batch_run, flag_vals)
    start_trial_run(run)
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


def expand_flags(flag_vals, random_seed=None):
    expanded = _expand_flags_base(flag_vals)
    _apply_flag_functions(expanded, random_seed)
    return expanded


def _expand_flags_base(flag_vals):
    """Expands flag vals without applying flag functions."""
    flags_list = [_expand_flag(name, val) for name, val in sorted(flag_vals.items())]
    return [dict(flags) for flags in itertools.product(*flags_list)]


def _expand_flag(name, val):
    if not isinstance(val, list):
        val = [val]
    return [(name, _flag_function_or_val(x, name)) for x in val]


def _flag_function_or_val(val, flag_name):
    if not isinstance(val, six.string_types):
        return val
    try:
        name, args = flag_util.decode_flag_function(val)
    except ValueError:
        return val
    else:
        return _FlagFunction(name, args, flag_name, val)


class _FlagFunction(object):
    def __init__(self, name, args, flag_name, flag_value):
        from guild.plugins import skopt_util

        self.dim, self.initial = skopt_util.function_dim(name, args, "dummy")
        self.flag_name = flag_name
        self.flag_value = flag_value
        self._applied_initial = False

    def apply(self, random_state):
        from guild.plugins import skopt_util

        if self.initial is not None and not self._applied_initial:
            self._applied_initial = True
            return self.initial

        try:
            res = skopt_util.skopt.dummy_minimize(
                lambda *args: 0, [self.dim], n_calls=1, random_state=random_state
            )
        except Exception as e:
            if log.getEffectiveLevel() <= logging.DEBUG:
                log.exception(
                    "apply flag function %s for %s with dim %s",
                    self.flag_value,
                    self.flag_name,
                    self.dim,
                )
            log.warning(
                "error applying function %s for flag %s: %s",
                self.flag_value,
                self.flag_name,
                e,
            )
            return None, random_state
        else:
            val = skopt_util.native_python_xs(res.x_iters[0])[0]
            return val, res.random_state


def _apply_flag_functions(trials, random_seed):
    random_state = random_seed
    for flag_vals in trials:
        for name, val in flag_vals.items():
            if isinstance(val, _FlagFunction):
                val, random_state = val.apply(random_state)
                flag_vals[name] = val


def expanded_batch_trials(batch_run, random_seed=None):
    proto_run = batch_run.batch_proto
    flag_vals = proto_run.get("flags") or {}
    trials = proto_run.get("trials")
    if trials:
        user_flag_vals = proto_run.get("user_flags") or {}
        return expand_trial_flags(trials, flag_vals, user_flag_vals, random_seed)
    else:
        return expand_flags(flag_vals, random_seed)


def expand_trial_flags(trials, flag_vals, user_flag_vals, random_seed=None):
    expanded = []
    for trial_flag_vals in trials:
        merged_flags = _merged_trial_flags(trial_flag_vals, flag_vals, user_flag_vals)
        expanded.extend(_expand_flags_base(merged_flags))
    _apply_flag_functions(expanded, random_seed)
    return expanded


def _merged_trial_flags(trial_flag_vals, flag_vals, user_flag_vals):
    merged = dict(flag_vals)
    merged.update(trial_flag_vals)
    merged.update(user_flag_vals)
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


def objective_scalar(batch_run, default=None):
    obj = batch_run.get("objective") or default or DEFAULT_OBJECTIVE
    if obj[0] == "-":
        return obj[1:], -1
    return obj, 1
