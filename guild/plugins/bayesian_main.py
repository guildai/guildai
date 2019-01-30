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

from . import skopt

DEFAULT_TRIALS = 20

def _gen_trials(flags, batch):
    num_trials = batch.max_trials or DEFAULT_TRIALS
    flag_names, dimensions = skopt.flag_dimensions(flags, _flag_dim)
    return [dict(zip(flag_names, dimensions))] * num_trials

def _flag_dim(val, flag_name):
    if isinstance(val, list):
        return val
    try:
        func_name, search_dim = batch_util.parse_function(val)
    except ValueError:
        return [val]
    else:
        _validate_search_dim(search_dim, func_name, flag_name)
        return search_dim

def _validate_search_dim(val, dist_name, flag_name):
    if dist_name not in (None, "search"):
        raise batch_util.BatchError(
            "unsupported function %r for flag %s - must be 'search'"
            % (dist_name, flag_name))
    if len(val) not in (2, 3):
        raise batch_util.BatchError(
            "unexpected arguemt list in %s for flag %s - "
            "expected 2 or 3 arguments" % (val, flag_name))

def _patch_numpy_deprecation_warnings():
    warnings.filterwarnings("ignore", category=Warning)
    import numpy.core.umath_tests

if __name__ == "__main__":
    _patch_numpy_deprecation_warnings()
    batch_util.default_main(_gen_trials)
