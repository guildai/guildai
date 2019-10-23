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

import six

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=Warning)
    import numpy.core.umath_tests

import skopt

from guild import flag_util

###################################################################
# Exceptions
###################################################################

class NoSearchDimensionError(Exception):

    def __init__(self, flag_vals):
        super(NoSearchDimensionError, self).__init__(flag_vals)
        self.flag_vals = flag_vals

class SearchDimensionError(Exception):
    pass

###################################################################
# Random trials
###################################################################

def random_trials_for_flags(flag_vals, count, random_seed=None):
    names, dims, _initials = flag_dims(flag_vals)
    if not names:
        raise NoSearchDimensionError(flag_vals)
    trials = _trials_for_dims(dims, names, count, random_seed)
    _apply_missing_flag_vals(flag_vals, trials)
    return trials

def _trials_for_dims(dims, names, num_trials, random_seed):
    res = skopt.dummy_minimize(
        lambda *args: 0,
        dims,
        n_calls=num_trials,
        random_state=random_seed)
    return [dict(zip(names, _native_python_xs(xs))) for xs in res.x_iters]

def _native_python_xs(xs):
    def pyval(x):
        try:
            return x.item()
        except AttributeError:
            return x
    return [pyval(x) for x in xs]

def _apply_missing_flag_vals(flag_vals, trials):
    for trial in trials:
        trial.update({
            name: flag_vals[name] for name in flag_vals
            if name not in trial
        })

###################################################################
# Flag dims
###################################################################

def flag_dims(flags):
    """Return flag names, dims, and initials for flags.

    Only flag value that correspond to searchable dimensions are
    returned. Scalars and non-function string values are not included
    in the result.
    """
    dims = {}
    initials = {}
    for name, val in flags.items():
        try:
            flag_dim, initial = _flag_dim(val, name)
        except ValueError:
            pass
        else:
            dims[name] = flag_dim
            initials[name] = initial
    names = sorted(dims)
    return (
        names,
        [dims[name] for name in names],
        [initials[name] for name in names])

def _flag_dim(val, flag_name):
    if isinstance(val, list):
        return _categorical_dim(val, None)
    elif isinstance(val, six.string_types):
        return _try_function_dim(val, flag_name)
    else:
        raise ValueError(val, flag_name)

def _categorical_dim(vals, initial):
    from skopt.space import space
    return space.Categorical(vals), initial

def _try_function_dim(val, flag_name):
    assert isinstance(val, six.string_types), val
    try:
        func_name, func_args = flag_util.decode_flag_function(val)
    except ValueError:
        raise ValueError(val, flag_name)
    else:
        return _function_dim(func_name, func_args, flag_name)

def _function_dim(func_name, args, flag_name):
    if func_name is None:
        func_name = "uniform"
    if func_name == "uniform":
        return _uniform_dim(args, func_name, flag_name)
    elif func_name == "loguniform":
        return _real_dim(args, "log-uniform", func_name, flag_name)
    else:
        raise SearchDimensionError(
            "unknown function '%s' used for flag %s"
            % (func_name, flag_name))

def _uniform_dim(args, func_name, flag_name):
    from skopt.space import space
    dim_args, initial = _dim_args_and_initial(args, func_name, flag_name)
    return space.check_dimension(dim_args), initial

def _real_dim(args, prior, func_name, flag_name):
    from skopt.space import space
    dim_args, initial = _dim_args_and_initial(args, func_name, flag_name)
    real_init_args = list(dim_args) + [prior]
    return space.Real(*real_init_args), initial

def _dim_args_and_initial(args, func_name, flag_name):
    if len(args) == 2:
        return args, None
    elif len(args) == 3:
        return args[:2], args[2]
    else:
        raise SearchDimensionError(
            "%s requires 2 or 3 args, got %s for flag %s"
            % (func_name, args, flag_name))
