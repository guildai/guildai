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

import os

import itertools

from guild import batch_util
from guild import batch_util2
from guild import op_util

def main():
    op_util.init_logging()
    proto_run = batch_util2.proto_run()
    proto_flags = proto_run.get("flags") or {}
    for trial_flag_vals in batch_util2.expand_flags(proto_flags):
        batch.run_trial(proto_run, trial_flag_vals)

# TODO: remove when promoting OP2
def gen_trials(flags, _batch=None):
    flag_list = [
        _trial_flags(name, val)
        for name, val in sorted(flags.items())]
    return [dict(trial) for trial in itertools.product(*flag_list)]

def _trial_flags(flag_name, flag_val):
    if isinstance(flag_val, list):
        return [(flag_name, trial_val) for trial_val in flag_val]
    return [(flag_name, flag_val)]

if __name__ == "__main__":
    if os.getenv("OP2") == "1":
        main()
    else:
        batch_util.default_main(gen_trials, default_max_trials=None)
