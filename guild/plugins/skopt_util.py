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

import collections
import logging
import sys
import warnings

import six

from guild import batch_util
from guild import index2
from guild import op_util
from guild import query

log = logging.getLogger("guild")

OptInputs = collections.namedtuple(
    "OptInputs", [
        "random_starts",
        "x0",
        "y0",
        "dims"
    ])

class State(batch_util.SeqState):

    def __init__(self, batch):
        super(State, self).__init__(batch)
        (self.dim_names,
         self.dims,
         self.initials) = flag_dims(self.proto_flags)
        self.run_index = index2.RunIndex()
        (self._run_loss,
         self.loss_desc) = _init_run_loss_fun(self.batch, self.run_index)
        self.random_state = batch.random_seed
        self._last_res = None

    def opt_inputs(self, trial_run_id):
        """Returns OptInputs for the state.

        Previous runs for the batch are used to calculate x0 and x0.

        Priority is given to the requested number of random starts in
        batch flags. If the number is larger than the number of
        previous trials, a random start is returned.

        If the number of requested random starts is less than or equal
        to the number of previous trials, previous trials are
        returned.

        If there are no previous trials, the dimensions are altered to
        include initial values and a random start is returned.

        """
        prev_trials = self.previous_trials(trial_run_id)
        log.info(
            "Found %i previous trial(s) for use in optimization",
            len(prev_trials))
        if self.batch_flags["random-starts"] > len(prev_trials):
            # Haven't met random-starts requirement yet - use a random
            # start.
            return OptInputs(1, None, None, self.dims)
        x0, y0 = self._split_prev_trials(prev_trials)
        if not x0:
            # No previous trials - use initial value if provided or
            # random start.
            return OptInputs(1, None, None, self._dims_with_initial())
        return OptInputs(0, x0, y0, self.dims)

    def previous_trials(self, trial_run_id):
        other_trial_runs = _prev_trial_candidates(self.batch, trial_run_id)
        if not other_trial_runs:
            return []
        trials = []
        self.run_index.refresh(other_trial_runs, ["scalar"])
        for run in other_trial_runs:
            loss = self._run_loss(run)
            if loss is None:
                raise batch_util.BatchError(
                    "could not get %r for run %s - quitting" %
                    (self.loss_desc, run.id))
            _try_append_prev_trial(run, self.dim_names, loss, trials)
        return trials

    def _split_prev_trials(self, trials):
        """Splits trials into x0 and y0.

        y0 is represented by the magic flag value `__loss__`, which is
        added to the trial prior to this split.
        """
        x0 = [[trial[name] for name in self.dim_names] for trial in trials]
        y0 = [trial["__loss__"] for trial in trials]
        return x0, y0

    def _dims_with_initial(self):
        """Returns dims with initial values where available.

        An initial value is represented by a single choice value in
        dims.
        """
        return [
            dim if initial is None else [initial]
            for dim, initial in zip(self.dims, self.initials)
        ]

    def update(self, optimized_result):
        self.random_state = optimized_result.random_state
        self._last_res = optimized_result

    def next_trial_flags(self):
        flags = {}
        flags.update(self.proto_flags)
        if self._last_res:
            suggestions = self._last_res.x_iters[-1]
            flags.update(trial_flags(self.dim_names, suggestions))
        return flags

def _init_run_loss_fun(batch, run_index):
    negate, col = _init_objective(batch)
    prefix, tag = col.split_key()
    def f(run):
        loss = run_index.run_scalar(
            run, prefix, tag, col.qualifier, col.step)
        if loss is None:
            return loss
        return loss * negate
    return f, str(col)

def _init_objective(batch):
    negate, colspec = _objective_colspec(batch)
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

def _prev_trial_candidates(batch, cur_trial_run_id):
    return [
        run for run in batch.seq_trial_runs(status="completed")
        if run.id != cur_trial_run_id
    ]

def _try_append_prev_trial(run, flag_names, loss, trials):
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

def trial_flags(names, vals):
    return dict(zip(names, _native_python(vals)))

def _native_python(l):
    def pyval(x):
        try:
            return x.item()
        except AttributeError:
            return x
    return [pyval(x) for x in l]

def default_main(seq_trial_cb, non_repeating=True):
    if non_repeating:
        seq_trial_cb = NonRepeatingTrials(seq_trial_cb)
    try:
        batch_util.seq_trials_main(seq_trial_cb, State)
    except batch_util.StopBatch as e:
        assert e.error
        sys.exit(1)

class NonRepeatingTrials(object):
    """Wrapper to ensure that seq trial callbacks don't repeat trials.

    If an skopt minimizer suggests a trial that we've already run,
    this wrapper uses dummy_minimize to generate a random trial within
    the state search space.
    """

    def __init__(self, seq_trial_cb):
        self.seq_trial_cb = seq_trial_cb

    def __call__(self, trial, state):
        _check_state_dims(state)
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
            state.dims,
            n_calls=1,
            random_state=state.random_state)
        state.update(res)
        return state.next_trial_flags()

    @staticmethod
    def _random_trial_label(trial, flag_desc):
        return "%s+random %s" % (trial.batch_label(), flag_desc)

def _check_state_dims(state):
    if not state.dim_names:
        flag_desc = ", ".join(op_util.flag_assigns(state.proto_flags))
        log.error(
            "flags for batch (%s) do not contain any search "
            "dimension - quitting", flag_desc)
        raise batch_util.StopBatch(error=True)

def flag_dims(flags):
    """Return flag names, dims, and initials for flags.

    Only flag value that correspond to searchable dimensions are
    returned. Scalars and non-function string values are not included
    in the result.
    """
    dims = {}
    initials = {}
    for name, val in flags.items():
        try:
            flag_dim, initial = _flag_dim(val, name)
        except ValueError:
            pass
        else:
            dims[name] = flag_dim
            initials[name] = initial
    names = sorted(dims)
    return (
        names,
        [dims[name] for name in names],
        [initials[name] for name in names])

def _flag_dim(val, flag_name):
    if isinstance(val, list):
        return _categorical_dim(val, None)
    elif isinstance(val, six.string_types):
        return _try_function_dim(val, flag_name)
    else:
        raise ValueError(val, flag_name)

def _categorical_dim(vals, initial):
    from skopt.space import space
    return space.Categorical(vals), initial

def _try_function_dim(val, flag_name):
    assert isinstance(val, six.string_types), val
    try:
        func_name, func_args = op_util.parse_function(val)
    except ValueError:
        raise ValueError(val, flag_name)
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

def _patch_numpy_deprecation_warnings():
    warnings.filterwarnings("ignore", category=Warning)
    # pylint: disable=unused-variable
    import numpy.core.umath_tests

_patch_numpy_deprecation_warnings()
