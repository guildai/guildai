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

from guild import model_proxy
from guild import op_util

from guild.optimizer import Optimizer

class RandomOptimizerModelProxy(model_proxy.BatchModelProxy):

    name = ""
    op_name = "random"
    module_name = "guild.optimizers.random_main"
    flag_encoder = "guild.optimizers.skopt:encode_flag_for_random"

def encode_flag_for_random(val, flagdef):
    fmt = op_util.format_flag_val
    if flagdef.choices:
        return [c.value for c in flagdef.choices]
    elif flagdef.min is not None and flagdef.max is not None:
        return "[%s:%s]" % (fmt(flagdef.min), fmt(flagdef.max))
    return val

class RandomOptimizer(Optimizer):

    @staticmethod
    def resolve_model_op(_opspec):
        model = RandomOptimizerModelProxy()
        return model, model.op_name

class BayesianOptimizer(Optimizer):

    @staticmethod
    def resolve_model_op(_opspec):
        assert False, "TODO"
