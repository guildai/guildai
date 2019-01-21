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

import re
import warnings

import six

from guild import batch_util
from guild import op_util

DEFAULT_TRIALS = 20

def _gen_trials(flags, batch):
    trials = batch.max_trials or DEFAULT_TRIALS
    random_seed = batch.random_seed
    flag_names, dimensions = _flag_dimensions(flags, batch)
    trial_vals = _gen_trial_vals(dimensions, trials, random_seed)
    return [
        dict(zip(flag_names, _native_python(flag_vals)))
        for flag_vals in trial_vals]

def _flag_dimensions(flags, batch):
    dims = {}
    _apply_flag_dims(flags, dims)
    _apply_proto_opdef_dims(batch, dims)
    names = sorted(dims)
    return names, [dims[name] for name in names]

def _apply_flag_dims(flags, dims):
    for name, val in flags.items():
        flag_dim = _flag_dim(val)
        if flag_dim != dims.get(name):
            dims[name] = flag_dim

def _flag_dim(val):
    if isinstance(val, list):
        return val
    try:
        return _parse_range(val)
    except ValueError:
        return [val]

def _parse_range(val):
    if not isinstance(val, six.string_types):
        raise ValueError()
    m = re.match(r"\[(.+?):(.+?)\]$", val.strip())
    if not m:
        raise ValueError()
    return (op_util.parse_arg_val(m.group(1)),
            op_util.parse_arg_val(m.group(2)))

def _apply_proto_opdef_dims(batch, dims):
    flags_data = batch.proto_opdef_data.get("flags")
    for name, flag_data in flags_data.items():
        if not isinstance(flag_data, dict):
            continue
        if not _flag_dim_unchanged(name, flag_data, dims):
            continue
        _apply_flag_config_dim(name, flag_data, dims)

def _flag_dim_unchanged(flag_name, config, dims):
    try:
        default = config["default"]
    except KeyError:
        return True
    else:
        # Dims for scalar vals X are expressed as [X]
        return dims.get(flag_name) == [default]

def _apply_flag_config_dim(flag_name, config, dims):
    for method in [_try_range, _try_choices]:
        config_dim = method(config)
        if config_dim is not None:
            dims[flag_name] = config_dim
            break

def _try_range(config):
    try:
        return config["min"], config["max"]
    except KeyError:
        return None

def _try_choices(config):
    try:
        choices = config["choices"]
    except KeyError:
        return None
    else:
        return [_choice_val(c) for c in choices]

def _choice_val(choice):
    if isinstance(choice, dict):
        return choice.get("value")
    return choice

def _gen_trial_vals(dimensions, trials, random_seed):
    import skopt
    res = skopt.dummy_minimize(
        lambda *args: 0,
        dimensions,
        n_calls=trials,
        random_state=random_seed)
    return res.x_iters

def _native_python(l):
    def pyval(x):
        try:
            return x.item
        except AttributeError:
            return x
    return [pyval(x) for x in l]

def _patch_numpy_deprecation_warnings():
    warnings.filterwarnings("ignore", category=Warning)
    import numpy.core.umath_tests

if __name__ == "__main__":
    _patch_numpy_deprecation_warnings()
    batch_util.default_main(_gen_trials)
