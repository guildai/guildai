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

# This module provides proxies for use by the core skopt facility,
# which is primarily implemented in skopt_utils. The proxies provide a
# minimal interface that can be used to generate new trial
# recommendations (flags) based on previous trial results.

from __future__ import absolute_import
from __future__ import division

import logging

from . import skopt_util

log = logging.getLogger("guild")

DEFAULT_MAX_TRIALS = 20

class RunProxy(object):

    # Run proxies are used for both batch runs and trial runs. In both
    # cases, runs must provide flags. In the case of batch runs, the
    # proxy must additionally provide an objective.

    def __init__(self, flags, objective=None):
        self.flags = flags
        self.objective = objective

    def get(self, name, _default=None):
        return getattr(self, name)

class BatchProxy(object):

    # ipy doesn't use batch runs so we have to proxy batch information
    # when using skopt_util facilities for skopt optimizers in ipy.

    def __init__(self, proto_flags, batch_flags, prev_runs,
                 random_seed=None, minimize=None, maximize=None,
                 **kw):
        if kw:
            log.warning("ignoring batch config: %s", kw)
        self.batch_run = RunProxy(batch_flags)
        objective = _init_objective(minimize, maximize)
        self.proto_run = RunProxy(proto_flags, objective)
        self.prev_runs = prev_runs
        self.random_seed = random_seed

    def seq_trial_runs(self, status=None):
        return [
            run for run in self.prev_runs
            if status is None or run.status == status]

def _init_objective(minimize, maximize):
    if minimize and maximize:
        raise ValueError("minimize and maximize cannot both be specified")
    if maximize:
        return {
            "maximize": maximize
        }
    return minimize

class TrialProxy(object):

    # Used by skopt_util State to get trial ID, which is used to
    # filter out the current trial from other batch files. Because
    # we're using the ipy interface, we get the explicit list of runs
    # from the gen_trials callback and so can safely ignore trial run
    # ID here.

    run_id = None

def gen_trials(init_trial, prev_runs, proto_flags, batch_flags,
               max_trials, label=None, **kw):

    # Function used by skopt optimizers to implement their get_trials
    # module callback. To generate suggested trials in ipy, which
    # doesn't use batch runs, we use skopt_util state with a batch
    # proxy. See above for more information.

    max_trials = max_trials or DEFAULT_MAX_TRIALS
    state = skopt_util.State(BatchProxy(
        proto_flags,
        batch_flags,
        prev_runs,
        **kw))
    trials = 0
    trial_opts = {
        "label": label
    }
    while trials < max_trials:
        trials += 1
        yield (init_trial(TrialProxy(), state), trial_opts)
