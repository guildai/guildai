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

from guild import batch_util
from guild import op_util


def main():
    op_util.init_logging()
    batch_run = batch_util.batch_run()
    trials = _batch_trials(batch_run)
    batch_util.handle_trials(batch_run, trials)


def _batch_trials(batch_run):
    random_seed = batch_run.get("random_seed")
    all_trials = batch_util.expanded_batch_trials(batch_run, random_seed)
    max_trials = batch_run.get("max_trials")
    if max_trials is None:
        return all_trials
    return batch_util.sample_trials(all_trials, max_trials, random_seed)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        batch_util.handle_system_exit(e)
