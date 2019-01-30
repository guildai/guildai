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
    fmt = op_util.format_flag_val
    if flagdef.choices:
        return [c.value for c in flagdef.choices]
    elif flagdef.min is not None and flagdef.max is not None:
        return "uniform(%s,%s)" % (fmt(flagdef.min), fmt(flagdef.max))
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
acq-optimizer:
  description: Method to minimize the acquistion function
  default: lbfgs
  choices: [auto, sampling, lbfgs]
inputs:
  description: >
    Path to a file containing a list of flags and associated scalar values

    The inputs are used by the optimizer as additional information when
    generating new trials.

    The file may be YAML or JSON and contain a top-level list of maps. Each
    map must include the flag names with associated values as well as a special
    name 'y0' with associated scalar value.
  type: existing-path
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
    return "search(%s)" % ",".join(args)

def flag_dimensions(flags, flag_dim_cb):
    dims = {
        name: flag_dim_cb(val, name)
        for name, val in flags.items()
    }
    names = sorted(dims)
    return names, [dims[name] for name in names]

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
