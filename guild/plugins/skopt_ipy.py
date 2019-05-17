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

DEFAULT_MAX_TRIALS = 20

class RunProxy(object):

    def __init__(self, flags):
        self.flags = flags

    def get(self, name, _default=None):
        if name == "flags":
            return self.flags
        elif name == "objective":
            return "xxx"
        assert False, name

class BatchProxy(object):

    def __init__(self, proto_flags, random_seed=None, **kw):
        # TODO: these batch flags come from the trial gen cb
        # (e.g. skopt_gp_main) - or the model op def.
        self.batch_run = RunProxy({
            "random-starts": 0,
            "acq-func": "gp_hedge",
            "kappa": 1.96,
            "xi": 0.01,
            "noise": "gaussian",
        })
        self.proto_run = RunProxy(proto_flags)
        self.random_seed = random_seed

    def seq_trial_runs(self, status=None):
        # TODO: lookup trials for - what trial?
        return []

class TrialProxy(object):

    run_id = None

def gen_trials(init_trial, flags, max_trials=None, **kw):
    max_trials = max_trials or DEFAULT_MAX_TRIALS
    state = skopt_util.State(BatchProxy(flags, **kw))
    trials = 0
    while trials < max_trials:
        trials += 1
        yield init_trial(TrialProxy(), state)
