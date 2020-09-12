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

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=Warning)
    import numpy.core.umath_tests  # pylint: disable=unused-import
    import skopt

from guild import batch_util

from . import skopt_util

log = logging.getLogger("guild")


def main():
    batch_util.init_logging()
    batch_run = batch_util.batch_run()
    skopt_util.handle_seq_trials(batch_run, _suggest_x)


def _suggest_x(dims, x0, y0, random_start, random_state, opts):
    res = skopt.forest_minimize(
        lambda *args: 0,
        dims,
        n_calls=1,
        n_random_starts=1 if random_start else 0,
        x0=x0,
        y0=y0,
        random_state=random_state,
        kappa=opts["kappa"],
        xi=opts["xi"],
    )
    return res.x_iters[-1], res.random_state


def gen_trials(
    flags, prev_results_cb, opt_random_starts=0, opt_kappa=1.96, opt_xi=0.01, **kw
):
    """ipy interface for trials."""
    return skopt_util.ipy_gen_trials(
        flags,
        prev_results_cb,
        _suggest_x,
        random_starts=opt_random_starts,
        suggest_x_opts={
            "kappa": opt_kappa,
            "xi": opt_xi,
        },
        **kw
    )


if __name__ == "__main__":
    main()
