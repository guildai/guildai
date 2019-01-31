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

import warnings

from guild import batch_util
from guild import index2

class State(object):

    def __init__(self, batch):
        self.batch = batch
        self.batch_flags = batch.batch_run.get("flags")
        (self.flag_names,
         self.flag_dims,
         self.defaults) = self._init_flag_dims(batch)
        self.run_index = index2.RunIndex()
        self.random_state = batch.random_seed

    def _init_flag_dims(self, batch):
        """Return flag names, dims, and defaults based on proto flags.

        A flag value in the form 'search=(min, max [, default])' may
        be used to specify a range with an optional default.
        """
        proto_flags = batch.proto_run.get("flags", {})
        dims = {}
        defaults = {}
        for name, val in proto_flags.items():
            flag_dim, default = self._flag_dim(val, name)
            dims[name] = flag_dim
            defaults[name] = default
        names = sorted(proto_flags)
        return (
            names,
            [dims[name] for name in names],
            [defaults[name] for name in names])

    @staticmethod
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

    def previous_trials(self, trial_run_id):
        other_trial_runs = self._previous_trial_run_candidates(trial_run_id)
        if not other_trial_runs:
            return []
        trials = []
        self.run_index.refresh(other_trial_runs, ["scalar"])
        for run in other_trial_runs:
            loss = self.run_index.run_scalar(run, None, "loss", "last", False)
            if loss is None:
                continue
            self._try_apply_previous_trial(run, self.flag_names, loss, trials)
        return trials

    def _previous_trial_run_candidates(self, cur_trial_run_id):
        trials = self.batch.read_index(filter_existing=True)
        other_trial_runs = [
            trial.trial_run(required=True)
            for trial in trials
            if trial.run_id != cur_trial_run_id
        ]
        return [
            run for run in other_trial_runs
            if run.status in ("completed", "terminated")
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
        previous_trials = self.previous_trials(trial_run_id)
        if self.batch_flags["random-starts"] > len(previous_trials):
            # Next run should use randomly generated values.
            return 1, None, None, self.flag_dims
        x0, y0 = self._split_previous_trials(previous_trials)
        if x0:
            return 0, x0, y0, self.flag_dims
        # No previous trials - use defaults where available with
        # randomly generated values.
        return 1, None, None, self._flag_dims_with_defaults()

    def _split_previous_trials(self, trials):
        """Splits trials into x0 and y0 based on flag names."""
        x0 = [[trial[name] for name in self.flag_names] for trial in trials]
        y0 = [trial["__loss__"] for trial in trials]
        return x0, y0

    def _flag_dims_with_defaults(self):
        """Returns flag dims with default values where available.

        A default value is represented by a single choice value in
        dims.
        """
        return [
            dim if default is None else [default]
            for default, dim in zip(self.defaults, self.flag_dims)
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
    import numpy.core.umath_tests

def default_main(iter_trials_cb):
    _patch_numpy_deprecation_warnings()
    batch_util.iter_trials_main(State, iter_trials_cb)
