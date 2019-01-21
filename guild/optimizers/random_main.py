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

from guild import batch_util

DEFAULT_TRIALS = 20

def _gen_trials(flags, batch):
    trials = batch.max_trials or DEFAULT_TRIALS
    random_seed = batch.random_seed
    flag_names, dimensions = _flag_dimensions(flags, batch)
    trial_vals = _random_vals(dimensions, trials, random_seed)
    return [
        dict(zip(flag_names, _native_python(flag_vals)))
        for flag_vals in trial_vals]

def _flag_dimensions(_flags, _batch):
    # TODO - lookup search spec from batch proto opdef
    return ["x"], [(-2.0, 2.0)]

def _random_vals(dimensions, trials, random_seed):
    import skopt
    res = skopt.dummy_minimize(
        lambda *args: 0,
        dimensions,
        n_calls=trials,
        random_state=random_seed)
    return res.x_iters

def _native_python(l):
    return [x.item() for x in l]

if __name__ == "__main__":
    batch_util.default_main(_gen_trials)
