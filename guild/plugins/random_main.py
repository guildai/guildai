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
from guild import op_util

from . import skopt_util

DEFAULT_TRIALS = 20

def _gen_trials(flags, batch):
    num_trials = batch.max_trials or DEFAULT_TRIALS
    random_seed = batch.random_seed
    flag_names, dims, _initials = skopt_util.flag_dims(flags)
    trial_vals = _gen_trial_vals(dims, num_trials, random_seed)
    return [
        skopt_util.trial_flags(flag_names, flag_vals)
        for flag_vals in trial_vals
    ]

def _flag_dims(flags):
    dims = {
        name: _flag_dim(val, name)
        for name, val in flags.items()
    }
    names = sorted(dims)
    return names, [dims[name] for name in names]

def _flag_dim(val, flag_name):
    if isinstance(val, list):
        return val
    try:
        dist_name, min_max = op_util.parse_function(val)
    except ValueError:
        return [val]
    else:
        _validate_min_max(min_max, dist_name, flag_name)
        return min_max

def _validate_min_max(val, dist_name, flag_name):
    if dist_name not in (None, "uniform"):
        raise batch_util.BatchError(
            "unsupported distribution %r for flag %s - must be 'uniform'"
            % (dist_name, flag_name))
    if len(val) != 2:
        raise batch_util.BatchError(
            "unexpected arguemt list %r for flag %s - expected 2 arguments"
            % (val, flag_name))

def _gen_trial_vals(dims, num_trials, random_seed):
    import skopt
    res = skopt.dummy_minimize(
        lambda *args: 0,
        dims,
        n_calls=num_trials,
        random_state=random_seed)
    return res.x_iters

def _patch_numpy_deprecation_warnings():
    warnings.filterwarnings("ignore", category=Warning)
    # pylint: disable=unused-variable
    import numpy.core.umath_tests

if __name__ == "__main__":
    _patch_numpy_deprecation_warnings()
    batch_util.default_main(_gen_trials)
