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
import sys

from guild import batch_util

from . import skopt_util

log = logging.getLogger("guild")

DEFAULT_MAX_TRIALS = 20


def main():
    batch_util.init_logging()
    batch_run = batch_util.batch_run()
    trials = _batch_trials(batch_run)
    batch_util.handle_trials(batch_run, trials)


def _batch_trials(batch_run):
    proto_flag_vals = batch_run.batch_proto.get("flags")
    batch_run = batch_util.batch_run()
    max_trials = batch_run.get("max_trials") or DEFAULT_MAX_TRIALS
    random_seed = batch_run.get("random_seed")
    try:
        return skopt_util.random_trials_for_flags(
            proto_flag_vals, max_trials, random_seed
        )
    except skopt_util.MissingSearchDimension as e:
        skopt_util.missing_search_dim_error(proto_flag_vals)
    except skopt_util.InvalidSearchDimension as e:
        _search_dim_error(e)


def _search_dim_error(e):
    log.error(str(e))
    sys.exit(1)


def gen_trials(flags, _prev_results, max_trials=None, random_seed=None, **_opts):
    """ipy interface for randomly generated trials."""
    return skopt_util.random_trials_for_flags(flags, max_trials, random_seed)


if __name__ == "__main__":
    main()
