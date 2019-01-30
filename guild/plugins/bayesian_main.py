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

import warnings

from guild import batch_util

DEFAULT_TRIALS = 20

class Trial(batch_util.Trial):

    def run(self, **kw):
        trial_run = self._trial_run(required=True)
        print("TODO:")
        print(" - collect inputs from batch flags and index")
        print("   %s" % self.batch.batch_run.get("flags"))
        print(" - collect search space from trial run flags")
        print("   %s" % self.batch.proto_run.get("flags"))
        print(" - feed to gp_min to get suggested xs")
        import random
        suggested = {"x": 1 + random.uniform(-1.0, 1.0)}
        trial_run.write_attr("flags", suggested)
        super(Trial, self).run(**kw)

    def __cmp__(self, trial):
        # If we haven't generated suggested flags for this trial yet,
        # consider not equal.
        if self.flags == {}:
            return -1
        return super(Trial, self).__cmp__(trial)

def _gen_trials(_flags, batch):
    num_trials = batch.max_trials or DEFAULT_TRIALS
    return [{}] * num_trials

"""
def _flag_dim(val, flag_name):
    import pdb;pdb.set_trace()
    if isinstance(val, list):
        return val
    try:
        func_name, search_dim = batch_util.parse_function(val)
    except ValueError:
        return [val]
    else:
        _validate_search_dim(search_dim, func_name, flag_name)
        return search_dim

def _validate_search_dim(val, dist_name, flag_name):
    if dist_name not in (None, "search"):
        raise batch_util.BatchError(
            "unsupported function %r for flag %s - must be 'search'"
            % (dist_name, flag_name))
    if len(val) not in (2, 3):
        raise batch_util.BatchError(
            "unexpected arguemt list in %s for flag %s - "
            "expected 2 or 3 arguments" % (val, flag_name))
"""

def _patch_numpy_deprecation_warnings():
    warnings.filterwarnings("ignore", category=Warning)
    import numpy.core.umath_tests

if __name__ == "__main__":
    _patch_numpy_deprecation_warnings()
    batch_util.default_main(_gen_trials, trial_cls=Trial)
