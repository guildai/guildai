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

import six

from guild import batch_util
from guild import index2
from guild import op_util
from guild import query

log = logging.getLogger("guild")

class State(object):

    def __init__(self, batch):
        self.batch = batch
        self.batch_flags = batch.batch_run.get("flags")
        proto_flags = batch.proto_run.get("flags", {})
        (self.flag_names,
         self.flag_dims,
         self.initials) = flag_dims(proto_flags)
        self.run_index = index2.RunIndex()
        (self._run_loss,
         self.loss_desc) = self._init_run_loss_fun(batch)
        self.random_state = batch.random_seed

    def _init_run_loss_fun(self, batch):
        negate, col = self._init_objective(batch)
        prefix, tag = col.split_key()
        def f(run):
            loss = self.run_index.run_scalar(
                run, prefix, tag, col.qualifier, col.step)
            if loss is None:
                return loss
            return loss * negate
        return f, str(col)

    def _init_objective(self, batch):
        negate, colspec = self._objective_colspec(batch)
        try:
            cols = query.parse_colspec(colspec).cols
        except query.ParseError as e:
            raise batch_util.BatchError(
                "cannot parse objective %r: %s" % (colspec, e))
        else:
            if len(cols) > 1:
                raise batch_util.BatchError(
                    "invalid objective %r: only one column may "
                    "be specified" % colspec)
            return negate, cols[0]

    @staticmethod
    def _objective_colspec(batch):
        objective = batch.proto_run.get("objective")
        if not objective:
            return 1, "loss"
        elif isinstance(objective, six.string_types):
            return 1, objective
        elif isinstance(objective, dict):
            minimize = objective.get("minimize")
            if minimize:
                return 1, minimize
            maximize = objective.get("maximize")
            if maximize:
                return -1, maximize
        raise batch_util.BatchError(
            "unsupported objective type %r"
            % objective)

    def previous_trials(self, trial_run_id):
        other_trial_runs = self._previous_trial_run_candidates(trial_run_id)
        if not other_trial_runs:
            return []
        trials = []
        self.run_index.refresh(other_trial_runs, ["scalar"])
        for run in other_trial_runs:
            loss = self._run_loss(run)
            if loss is None:
                raise batch_util.BatchError(
                    "could not get %r for run %s, quitting" %
                    (self.loss_desc, run.id))
            self._try_apply_previous_trial(run, self.flag_names, loss, trials)
        return trials

    def _previous_trial_run_candidates(self, cur_trial_run_id):
        return [
            run
            for run in self.batch.seq_trial_runs(status="completed")
            if run.id != cur_trial_run_id
        ]

    @staticmethod
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

    def minimize_inputs(self, trial_run_id):
        """Returns random_starts, x0, y0 and dims given a host of inputs.

        Priority is given to the requested number of random starts in
        batch flags. If the number is larger than the number of
        previous trials, a random start is returned.

        If the number of requested random starts is less than or equal
        to the number of previous trials, previous trials are
        returned.

        If there are no previous trials, the dimensions are altered to
        include initial values and a random start is returned.
        """
        previous_trials = self.previous_trials(trial_run_id)
        log.info(
            "Found %i previous trial(s) for use in optimization",
            len(previous_trials))
        if self.batch_flags["random-starts"] > len(previous_trials):
            # Next run should use randomly generated values.
            return 1, None, None, self.flag_dims
        x0, y0 = self._split_previous_trials(previous_trials)
        if not x0:
            # No previous trials - use initial value if provided or
            # random start.
            return 1, None, None, self._flag_dims_with_initial()
        return 0, x0, y0, self.flag_dims

    def _split_previous_trials(self, trials):
        """Splits trials into x0 and y0 based on flag names."""
        x0 = [[trial[name] for name in self.flag_names] for trial in trials]
        y0 = [trial["__loss__"] for trial in trials]
        return x0, y0

    def _flag_dims_with_initial(self):
        """Returns flag dims with initial values where available.

        An initial value is represented by a single choice value in
        dims.
        """
        return [
            dim if initial is None else [initial]
            for dim, initial in zip(self.flag_dims, self.initials)
        ]

def trial_flags(flag_names, flag_vals):
    return dict(zip(flag_names, _native_python(flag_vals)))

def _native_python(l):
    def pyval(x):
        try:
            return x.item()
        except AttributeError:
            return x
    return [pyval(x) for x in l]

def _patch_numpy_deprecation_warnings():
    warnings.filterwarnings("ignore", category=Warning)
    # pylint: disable=unused-variable
    import numpy.core.umath_tests

def default_main(seq_trial_cb, non_repeating=True):
    _patch_numpy_deprecation_warnings()
    if non_repeating:
        seq_trial_cb = NonRepeatingTrials(seq_trial_cb)
    batch_util.seq_trials_main(State, seq_trial_cb)

class NonRepeatingTrials(object):
    """Wrapper to ensure that seq trial callbacks don't repeat trials.

    If an skopt minimizer suggests a trial that we've already run,
    this wrapper uses dummy_minimize to generate a random trial within
    the state search space.
    """

    def __init__(self, seq_trial_cb):
        self.seq_trial_cb = seq_trial_cb

    def __call__(self, trial, state):
        next_trial_flags = self.seq_trial_cb(trial, state)
        for run in trial.batch.seq_trial_runs():
            if next_trial_flags == run.get("flags"):
                flag_desc = " ".join(op_util.flag_assigns(next_trial_flags))
                log.warning(
                    "optimizer repeated trial (%s) - using random",
                    flag_desc)
                return (
                    self._random_trial(state),
                    {"label": self._random_trial_label(trial, flag_desc)})
        return next_trial_flags, {}

    @staticmethod
    def _random_trial(state):
        import skopt
        res = skopt.dummy_minimize(
            lambda *args: 0,
            state.flag_dims,
            n_calls=1,
            random_state=state.random_state)
        state.random_state = res.random_state
        return trial_flags(state.flag_names, res.x_iters[-1])

    @staticmethod
    def _random_trial_label(trial, flag_desc):
        return "%s+random %s" % (trial.batch_label(), flag_desc)

def flag_dims(flags):
    """Return flag names, dims, and initials for flags.
    """
    dims = {}
    initials = {}
    for name, val in flags.items():
        flag_dim, initial = _flag_dim(val, name)
        dims[name] = flag_dim
        initials[name] = initial
    names = sorted(flags)
    return (
        names,
        [dims[name] for name in names],
        [initials[name] for name in names])

def _flag_dim(val, flag_name):
    _patch_numpy_deprecation_warnings()
    from skopt.space import space
    if isinstance(val, list):
        return space.Categorical(val), None
    try:
        func_name, func_args = op_util.parse_function(val)
    except ValueError:
        return space.Categorical([val]), val
    else:
        return _function_dim(func_name, func_args, flag_name)

def _function_dim(func_name, args, flag_name):
    if func_name is None:
        func_name = "uniform"
    if func_name == "uniform":
        return _uniform_dim(args, func_name, flag_name)
    elif func_name == "loguniform":
        return _real_dim(args, "log-uniform", func_name, flag_name)
    raise batch_util.BatchError(
        "unsupported function %r for flag %s"
        % (func_name, flag_name))

def _uniform_dim(args, func_name, flag_name):
    from skopt.space import space
    if len(args) == 2:
        dim_args = args
        initial = None
    elif len(args) == 3:
        dim_args = args[:2]
        initial = args[2]
    else:
        raise batch_util.BatchError(
            "%s requires 2 or 3 args, got %r for flag %s"
            % (func_name, args, flag_name))
    return space.check_dimension(dim_args), initial

def _real_dim(args, prior, func_name, flag_name):
    from skopt.space import space
    if len(args) == 2:
        dim_args = args
        initial = None
    elif len(args) == 3:
        dim_args = args[:2]
        initial = args[2]
    else:
        raise batch_util.BatchError(
            "%s requires 2 or 3 args, got %r for flag %s"
            % (func_name, args, flag_name))
    real_init_args = list(dim_args) + [prior]
    return space.Real(*real_init_args), initial
