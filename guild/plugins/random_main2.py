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
import sys

from guild import batch_util2 as batch_util
from guild import op_util2 as op_util

from . import skopt_util2 as skopt_util

log = logging.getLogger("guild")

DEFAULT_MAX_TRIALS = 20

def main():
    op_util.init_logging()
    proto_run = batch_util.proto_run()
    trials = _batch_trials(proto_run)
    batch_util.handle_trials(proto_run, trials)

def _batch_trials(proto_run):
    flag_vals = proto_run.get("flags")
    batch_run = batch_util.batch_run()
    max_trials = batch_run.get("max_trials") or DEFAULT_MAX_TRIALS
    random_seed = batch_run.get("random_seed")
    try:
        return skopt_util.random_trials_for_flags(
            flag_vals,
            max_trials,
            random_seed)
    except skopt_util.NoSearchDimensionError as e:
        _no_search_dim_error(e.flag_vals)
    except skopt_util.SearchDimensionError as e:
        _search_dim_error(e)

def _no_search_dim_error(flag_vals):
    log.error(
        "flags for batch (%s) do not contain any search dimensions\n"
        "Try specifying a range for one or more flags as NAME=[MIN:MAX].",
        op_util.flags_desc(flag_vals))
    sys.exit(1)

def _search_dim_error(e):
    log.error(str(e))
    sys.exit(1)

if __name__ == "__main__":
    main()
