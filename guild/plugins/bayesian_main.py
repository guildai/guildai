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

import logging
import warnings

from guild import batch_util
from guild import index2

from . import skopt_util

log = logging.getLogger("guild")

DEFAULT_TRIALS = 20

class State(object):

    def __init__(self, batch):
        self.batch = batch
        (self.flag_names,
         self.flag_dims,
         self.defaults) = _flag_dims(batch)
        self.run_index = index2.RunIndex()
        self.random_state = batch.random_seed

def _flag_dims(batch):
    """Return flag names, dims, and defaults based on proto flags.

    A flag value in the form 'search=(min, max [, default])' may
    be used to specify a range with an optional default.
    """
    proto_flags = batch.proto_run.get("flags", {})
    dims = {}
    defaults = {}
    for name, val in proto_flags.items():
        flag_dim, default = _flag_dim(val, name)
        dims[name] = flag_dim
        defaults[name] = default
    names = sorted(proto_flags)
    return (
        names,
        [dims[name] for name in names],
        [defaults[name] for name in names])

def _flag_dim(val, flag_name):
    if isinstance(val, list):
        return val, None
    try:
        func_name, search_dim = batch_util.parse_function(val)
    except ValueError:
        return [val], None
    else:
        if func_name not in (None, "search"):
            raise batch_util.BatchError(
                "unsupported function %r for flag %s - must be 'search'"
                % (func_name, flag_name))
        if len(search_dim) == 2:
            return search_dim, None
        elif len(search_dim) == 3:
            return search_dim[:2], search_dim[2]
        else:
            raise batch_util.BatchError(
                "unexpected arguemt list in %s for flag %s - "
                "expected 2 arguments" % (val, flag_name))

def _init_trial(trial, state):
    return _next_flags(trial, state)

def _next_flags(trial, state):
    """Return a next set of trial flags given previous trial data.

    If there is no previous trial data, we provide a set of starting
    flags based on the proto flags. In cases where defaults are
    provided, those are used, otherwise random values are generated
    based on the flag search space.
    """
    import skopt
    batch_flags = state.batch.batch_run.get("flags")
    previous_trials = _previous_trials(trial.run_id, state)
    random_starts, x0, y0, dims = _inputs(batch_flags, previous_trials, state)
    res = skopt.gp_minimize(
        lambda *args: 0,
        dims,
        n_calls=1,
        n_random_starts=random_starts,
        x0=x0,
        y0=y0,
        random_state=state.random_state,
        acq_func=batch_flags["acq-func"],
        kappa=batch_flags["kappa"],
        xi=batch_flags["xi"],
        noise=batch_flags["noise"])
    state.random_state = res.random_state
    return skopt_util.trial_flags(state.flag_names, res.x_iters[-1])

def _previous_trials(trial_run_id, state):
    other_trial_runs = _previous_trial_run_candidates(trial_run_id, state)
    if not other_trial_runs:
        return []
    trials = []
    state.run_index.refresh(other_trial_runs, ["scalar"])
    for run in other_trial_runs:
        loss = state.run_index.run_scalar(run, None, "loss", "last", False)
        if loss is None:
            continue
        _try_apply_previous_trial(run, state.flag_names, loss, trials)
    return trials

def _previous_trial_run_candidates(cur_trial_run_id, state):
    trials = state.batch.read_index(filter_existing=True)
    other_trial_runs = [
        trial.trial_run(required=True)
        for trial in trials
        if trial.run_id != cur_trial_run_id
    ]
    return [
        run for run in other_trial_runs
        if run.status in ("completed", "terminated")
    ]

def _try_apply_previous_trial(run, flag_names, loss, trials):
    run_flags = run.get("flags", {})
    try:
        trial = {
            name: run_flags[name]
            for name in flag_names
        }
    except KeyError:
        pass
    else:
        trial["__loss__"] = loss
        trials.append(trial)

def _inputs(batch_flags, previous_trials, state):
    """Returns random starts, x0, y0 and dims given a host of inputs.

    Priority is given to the requested number of random starts in
    batch flags. If the number is larger than the number of
    previous trials, a random start is returned.

    If the number of requested random starts is less than or equal
    to the number of previous trials, previous trials are
    returned.

    If there are no previous trials, the dimensions are altered to
    include default values and a random start is returned.
    """
    if batch_flags["random-starts"] > len(previous_trials):
        # Next run should use randomly generated values.
        return 1, None, None, state.flag_dims
    x0, y0 = _split_previous_trials(previous_trials, state.flag_names)
    if x0:
        return 0, x0, y0, state.flag_dims
    # No previous trials - use defaults where available with
    # randomly generated values.
    return 1, None, None, _apply_defaults(state)

def _split_previous_trials(trials, flag_names):
    """Splits trials into x0 and y0 based on flag names."""
    x0 = [[trial[name] for name in flag_names] for trial in trials]
    y0 = [trial["__loss__"] for trial in trials]
    return x0, y0

def _apply_defaults(state):
    """Applies default values when available to dims.

    A default value is represented by a single choice value in
    dims.
    """
    return [
        dim if default is None else [default]
        for default, dim in zip(state.defaults, state.flag_dims)
    ]

def _patch_numpy_deprecation_warnings():
    warnings.filterwarnings("ignore", category=Warning)
    import numpy.core.umath_tests

if __name__ == "__main__":
    _patch_numpy_deprecation_warnings()
    batch_util.iter_trials_main(State, _init_trial)
