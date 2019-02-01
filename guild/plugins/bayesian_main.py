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

from . import skopt_util

def _init_trial(trial, state):
    import skopt
    random_starts, x0, y0, dims = state.minimize_inputs(trial.run_id)
    res = skopt.gp_minimize(
        lambda *args: 0,
        dims,
        n_calls=1,
        n_random_starts=random_starts,
        x0=x0,
        y0=y0,
        random_state=state.random_state,
        acq_func=state.batch_flags["acq-func"],
        kappa=state.batch_flags["kappa"],
        xi=state.batch_flags["xi"],
        noise=state.batch_flags["noise"])
    state.random_state = res.random_state
    return skopt_util.trial_flags(state.flag_names, res.x_iters[-1])

if __name__ == "__main__":
    skopt_util.default_main(_init_trial)
