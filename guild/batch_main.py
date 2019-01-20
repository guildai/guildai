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

import itertools
import logging
import os

from guild import batch_util
from guild import op_util

log = logging.getLogger("guild")

def main():
    op_util.init_logging()
    batch = batch_util.init_batch()
    trials = _generate_trials(batch)
    if os.getenv("PRINT_TRIALS") == "1":
        batch_util.print_trials(trials)
    else:
        _init_pending(trials)
        _run(trials)

def _generate_trials(batch):
    return batch.sample_trials(_all_trials(batch))

def _all_trials(batch):
    trials = []
    base_flags = batch.proto_run.get("flags") or {}
    batches = batch.proto_run.get("batches") or []
    if batches:
        _acc_batch_trials(base_flags, batches, trials)
    else:
        _acc_trials(base_flags, trials)
    return [batch_util.Trial(batch, dict(flags)) for flags in trials]

def _acc_batch_trials(base_flags, batches, trials):
    for batch_flags in batches:
        _acc_trials(_join_flags(base_flags, batch_flags), trials)

def _join_flags(base, extra):
    joined = {}
    joined.update(base)
    joined.update(extra)
    return joined

def _acc_trials(flags, trials):
    flag_list = [
        _trial_flags(name, val)
        for name, val in sorted(flags.items())]
    for trial in itertools.product(*flag_list):
        trials.append(trial)

def _trial_flags(flag_name, flag_val):
    if isinstance(flag_val, list):
        return [(flag_name, trial_val) for trial_val in flag_val]
    return [(flag_name, flag_val)]

def _init_pending(trials):
    for trial in trials:
        if not trial.initialized:
            trial.init()

def _run(trials):
    for trial in trials:
        if trial.run_deleted:
            assert trials.run_id
            log.info("trial %s deleted, skipping", trial.run_id)
        trial.run()

if __name__ == "__main__":
    main()
