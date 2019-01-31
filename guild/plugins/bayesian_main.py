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

class Trial(batch_util.Trial):

    def init(self, run_dir=None, quiet=False):
        """Initialize a bayseian optimization trial.

        Overrides default to lookup previous trial results and use
        those to generate a next set of trial flags based on skopts's
        gp_minimize function.
        """
        super(Trial, self).init(run_dir, quiet=True)
        self.flags = self._next_trial_flags()
        self._write_trial_flags(self.flags)
        if not quiet:
            trial_run = self.trial_run(required=True)
            log.info(
                "Initialized trial %s (%s)", self._run_desc(trial_run),
                ", ".join(self._flag_assigns()))

    def config_equals(self, trial):
        """Return True if trial config equals our config.

        Used to determine whether or not to re-run a trial. It
        important that we indicate inequality when our flags are in
        not yet initialized to ensure that we're run.
        """
        if self.flags == {}:
            return False
        return super(Trial, self).config_equals(trial)

    def _next_trial_flags(self):
        """Return a next set of trial flags given previous trial data.

        If there is no previous trial data, we provide a set of
        starting flags based on the proto flags. In cases where
        defaults are provided, those are used, otherwise random values
        are generated based on the flag search space.
        """
        import skopt
        batch_flags = self.batch.batch_run.get("flags")
        assert batch_flags, batch_flags
        flag_names, flag_dims, defaults = self._flag_dims()
        previous_trials = self._previous_trials(flag_names)
        random_starts, x0, y0, dims = self._inputs(
            batch_flags, previous_trials, flag_names,
            defaults, flag_dims)
        res = skopt.gp_minimize(
            lambda *args: 0,
            dims,
            n_calls=1,
            n_random_starts=random_starts,
            x0=x0,
            y0=y0,
            random_state=self.batch._random_state,
            acq_func=batch_flags["acq-func"],
            kappa=batch_flags["kappa"],
            xi=batch_flags["xi"],
            noise=batch_flags["noise"])
        self.batch._random_state = res.random_state
        return skopt_util.trial_flags(flag_names, res.x_iters[-1])

    def _flag_dims(self):
        # Use cached value set in _gen_trials.
        return self.batch._trial_dims

    def _previous_trials(self, flag_names):
        other_trial_runs = self._previous_trial_run_candidates()
        if not other_trial_runs:
            return []
        trials = []
        index = self.batch._run_index
        index.refresh(other_trial_runs, ["scalar"])
        for run in other_trial_runs:
            loss = index.run_scalar(run, None, "loss", "last", False)
            if loss is None:
                continue
            self._try_apply_previous_trial(run, flag_names, loss, trials)
        return trials

    def _previous_trial_run_candidates(self):
        trials = self.batch.read_index(filter_existing=True)
        other_trial_runs = [
            trial.trial_run(required=True)
            for trial in trials
            if trial.run_id != self.run_id
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

    def _inputs(self, batch_flags, previous_trials, flag_names, defaults, dims):
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
            return 1, None, None, dims
        x0, y0 = self._split_previous_trials(previous_trials, flag_names)
        if x0:
            return 0, x0, y0, dims
        # No previous trials - use defaults where available with
        # randomly generated values.
        return 1, None, None, self._apply_defaults(defaults, dims)

    @staticmethod
    def _split_previous_trials(trials, flag_names):
        """Splits trials into x0 and y0 based on flag names."""
        x0 = [[trial[name] for name in flag_names] for trial in trials]
        y0 = [trial["__loss__"] for trial in trials]
        return x0, y0

    @staticmethod
    def _apply_defaults(defaults, dims):
        """Applies default values when available to dims.

        A default value is represented by a single choice value in
        dims.
        """
        return [
            dim if default is None else [default]
            for default, dim in zip(defaults, dims)
        ]

    def _write_trial_flags(self, flags):
        trial_run = self.trial_run(required=True)
        trial_run.write_attr("flags", flags)

def _gen_trials(_flags, batch):
    batch._trial_dims = _flag_dims(batch)
    batch._run_index = index2.RunIndex()
    batch._random_state = batch.random_seed
    num_trials = batch.max_trials or DEFAULT_TRIALS
    return [{}] * num_trials

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

def _patch_numpy_deprecation_warnings():
    warnings.filterwarnings("ignore", category=Warning)
    import numpy.core.umath_tests

if __name__ == "__main__":
    _patch_numpy_deprecation_warnings()
    batch_util.default_main(_gen_trials, trial_cls=Trial)
