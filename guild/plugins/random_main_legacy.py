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

import logging
import warnings

from guild import batch_util
from guild import op_util

from . import skopt_util_legacy as skopt_util

log = logging.getLogger("guild")

DEFAULT_TRIALS = 20


def gen_trials(flags, _runs, max_trials=None, random_seed=None, label=None, **kw):
    """Public interface for ipy."""
    if kw:
        log.warning("ignoring configuration %s", kw)
    num_trials = max_trials or DEFAULT_TRIALS
    dim_names, dims, _initials = skopt_util.flag_dims(flags)
    if not dim_names:
        log.error(
            "flags for batch (%s) do not contain any search " "dimension - quitting",
            op_util.flags_desc(flags),
        )
        raise batch_util.StopBatch(error=True)
    trial_vals = _gen_trial_vals(dims, num_trials, random_seed)
    trial_opts = {"label": label or "random"}
    return [
        (_trial_flags(dim_names, dim_vals, flags), trial_opts)
        for dim_vals in trial_vals
    ]


def _gen_trial_vals(dims, num_trials, random_seed):
    import skopt

    res = skopt.dummy_minimize(
        lambda *args: 0, dims, n_calls=num_trials, random_state=random_seed
    )
    return res.x_iters


def _trial_flags(dim_names, dim_vals, base_flags):
    trial_flags = {}
    trial_flags.update(base_flags)
    trial_flags.update(skopt_util.trial_flags(dim_names, dim_vals))
    return trial_flags


def _gen_batch_trials(flags, batch):
    trials = gen_trials(flags, None, batch.max_trials, batch.random_seed)
    return [t[0] for t in trials]


def _patch_numpy_deprecation_warnings():
    warnings.filterwarnings("ignore", category=Warning)
    # pylint: disable=unused-variable
    import numpy.core.umath_tests


if __name__ == "__main__":
    _patch_numpy_deprecation_warnings()
    batch_util.default_main(_gen_batch_trials)
