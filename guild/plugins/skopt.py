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

import yaml

from guild import model_proxy
from guild import op_util
from guild import plugin as pluginlib

###################################################################
# Random optimizer
###################################################################

class RandomOptimizerModelProxy(model_proxy.BatchModelProxy):

    name = "skopt"
    op_name = "random"
    op_description = (
        "Batch processor supporting random flag value generation.")
    module_name = "guild.plugins.random_main"
    flag_encoder = "guild.plugins.skopt:encode_flag_for_optimizer"

###################################################################
# Bayesian with gaussian process optimizer
###################################################################

class GPOptimizerModelProxy(model_proxy.BatchModelProxy):

    name = "skopt"
    op_name = "gp"
    op_description = yaml.safe_load(""">

  Bayesian optimizer using Gaussian processes.

  Refer to https://scikit-optimize.github.io/#skopt.gp_minimize for
  details on this algorithm and its flags.
  """)

    module_name = "guild.plugins.skopt_gp_main"
    flag_encoder = "guild.plugins.skopt:encode_flag_for_optimizer"

    flags_data = yaml.safe_load("""
random-starts:
  description: Number of trials using random values before optimizing
  default: 0
  type: int
acq-func:
  description: Function to minimize over the gaussian prior
  default: gp_hedge
  choices:
    - value: LCB
      description: Lower confidence bound
    - value: EI
      description: Negative expected improvement
    - value: PI
      description: Negative probability of improvement
    - value: gp_hedge
      description: Probabilistically use LCB, EI, or PI at every iteration
    - value: EIps
      description: Negative expected improvement per second
    - value: PIps
      description: Negative probability of improvement per second
kappa:
  description:
    Degree to which variance in the predicted values is taken into account
  default: 1.96
  type: float
xi:
  description: Improvement to seek over the previous best values
  default: 0.01
  type: float
noise:
  description:
    Level of noise associated with the objective

    Use 'gaussian' if the objective returns noisy observations, otherwise
    specify the expected variance of the noise.
  default: gaussian
""")

###################################################################
# Forest optimizer
###################################################################

class ForestOptimizerModelProxy(model_proxy.BatchModelProxy):

    name = "skopt"
    op_name = "forest"
    op_description = yaml.safe_load(""">

  Sequential optimization using decision trees.
  Refer to https://scikit-optimize.github.io/#skopt.forest_minimize
  for details on this algorithm and its flags.
  """)

    module_name = "guild.plugins.skopt_forest_main"
    flag_encoder = "guild.plugins.skopt:encode_flag_for_optimizer"

    flags_data = yaml.safe_load("""
random-starts:
  description: Number of trials using random values before optimizing
  default: 0
  type: int
kappa:
  description:
    Degree to which variance in the predicted values is taken into account
  default: 1.96
  type: float
xi:
  description: Improvement to seek over the previous best values
  default: 0.01
  type: float
""")

###################################################################
# Gradient boosted regression tree (GBRT) optimizer
###################################################################

class GBRTOptimizerModelProxy(model_proxy.BatchModelProxy):

    name = "skopt"
    op_name = "gbrt"
    op_description = yaml.safe_load(""">

  Sequential optimization using gradient boosted regression trees.

  Refer to https://scikit-optimize.github.io/#skopt.gbrt_minimize
  for details on this algorithm and its flags.
  """)

    module_name = "guild.plugins.skopt_gbrt_main"
    flag_encoder = "guild.plugins.skopt:encode_flag_for_optimizer"

    flags_data = yaml.safe_load("""
random-starts:
  description: Number of trials using random values before optimizing
  default: 0
  type: int
kappa:
  description:
    Degree to which variance in the predicted values is taken into account
  default: 1.96
  type: float
xi:
  description: Improvement to seek over the previous best values
  default: 0.01
  type: float
""")

###################################################################
# Flag encoders
###################################################################

def encode_flag_for_optimizer(val, flagdef):
    """Encodes a flag def for the range of supported skopt search spaces.
    """
    if flagdef.choices:
        return [c.value for c in flagdef.choices]
    elif flagdef.min is not None and flagdef.max is not None:
        return _encode_function(flagdef, val)
    return val

def _encode_function(flagdef, val):
    assert flagdef.min is not None and flagdef.max is not None
    func_name = flagdef.distribution or "uniform"
    low = op_util.format_flag_val(flagdef.min)
    high = op_util.format_flag_val(flagdef.max)
    args = [low, high]
    if val is not None:
        initial = op_util.format_flag_val(val)
        args.append(initial)
    return "%s[%s]" % (func_name, ":".join(args))

###################################################################
# Plugin
###################################################################

class SkoptPlugin(pluginlib.Plugin):

    @staticmethod
    def resolve_model_op(opspec):
        if opspec in ("random", "skopt:random"):
            model = RandomOptimizerModelProxy()
            return model, model.op_name
        elif opspec in ("gp", "skopt:gp", "bayesian", "gaussian"):
            model = GPOptimizerModelProxy()
            return model, model.op_name
        elif opspec in ("forest", "skopt:forest"):
            model = ForestOptimizerModelProxy()
            return model, model.op_name
        elif opspec in ("gbrt", "skopt:gbrt"):
            model = GBRTOptimizerModelProxy()
            return model, model.op_name
        return None
