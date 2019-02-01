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

class RandomOptimizerModelProxy(model_proxy.BatchModelProxy):

    name = "skopt"
    op_name = "random"
    op_description = (
        "Batch processor supporting random flag value generation.")
    module_name = "guild.plugins.random_main"
    flag_encoder = "guild.plugins.skopt:encode_flag_for_random"

def encode_flag_for_random(val, flagdef):
    """Encodes a flag def as either a list or a slice range.

    A slice range is used to convey a range from MIN to MAX. It's
    typically used for a uniform random distribution with min and max
    values.
    """
    if flagdef.choices:
        return [c.value for c in flagdef.choices]
    elif flagdef.min is not None and flagdef.max is not None:
        return (flagdef.min, flagdef.max)
    return val

class BayesianOptimizerModelProxy(model_proxy.BatchModelProxy):

    name = ""
    op_name = "bayesian"
    op_description = yaml.safe_load(""">

  Bayesian optimizer using Gaussian processes.

  Refer to https://scikit-optimize.github.io/#skopt.gp_minimize for
  details on this algorithm and its flags.
  """)

    module_name = "guild.plugins.bayesian_main"
    flag_encoder = "guild.plugins.skopt:encode_flag_for_bayesian"

    flags_data = yaml.safe_load("""
random-starts:
  description: Number of trials using random values before optimizing.
  default: 0
  type: int
acq-func:
  description: Function to minimize over the gaussian prior.
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

def encode_flag_for_bayesian(val, flagdef):
    """Encodes a flag def for the full range of supported skopt search spaces.
    """
    if flagdef.choices:
        return [c.value for c in flagdef.choices]
    elif flagdef.min is not None and flagdef.max is not None:
        return _encode_search(flagdef, val)
    return val

def _encode_search(flagdef, val):
    assert flagdef.min is not None and flagdef.max is not None
    args = [
        op_util.format_flag_val(flagdef.min),
        op_util.format_flag_val(flagdef.max)
    ]
    if val is not None:
        args.append(op_util.format_flag_val(val))
    return "uniform(%s)" % ",".join(args)

class SkoptPlugin(pluginlib.Plugin):

    @staticmethod
    def resolve_model_op(opspec):
        if opspec in ("random", "skopt:random"):
            model = RandomOptimizerModelProxy()
            return model, model.op_name
        elif opspec in ("bayesian", "skopt:bayesian"):
            model = BayesianOptimizerModelProxy()
            return model, model.op_name
        return None
