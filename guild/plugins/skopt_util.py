# Copyright 2017-2020 TensorHub, Inc.
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

import logging
import os
import warnings

import six

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=Warning)
    import numpy.core.umath_tests  # pylint: disable=unused-import
    import skopt

from guild import batch_util
from guild import flag_util
from guild import op_util
from guild import query as qparse

log = logging.getLogger("guild")

DEFAULT_MAX_TRIALS = 20
DEFAULT_OBJECTIVE = "loss"

###################################################################
# Exceptions
###################################################################


class MissingSearchDimension(Exception):
    def __init__(self, flag_vals):
        super(MissingSearchDimension, self).__init__(flag_vals)
        self.flag_vals = flag_vals


class InvalidSearchDimension(Exception):
    pass


class InvalidObjective(Exception):
    pass


###################################################################
# Random trials
###################################################################


def random_trials_for_flags(flag_vals, count, random_seed=None):
    names, dims, initial_x = flag_dims(flag_vals)
    if not names:
        raise MissingSearchDimension(flag_vals)
    trials = _trials_for_dims(names, dims, initial_x, count, random_seed)
    _apply_missing_flag_vals(flag_vals, trials)
    return trials


def _trials_for_dims(names, dims, initial_x, num_trials, random_seed):
    res = skopt.dummy_minimize(
        lambda *args: 0, dims, n_calls=num_trials, random_state=random_seed
    )
    trials_xs = res.x_iters
    if trials_xs:
        _apply_initial_x(initial_x, trials_xs[0])
    return [dict(zip(names, _native_python_xs(xs))) for xs in trials_xs]


def _native_python_xs(xs):
    def pyval(x):
        try:
            return x.item()
        except AttributeError:
            return x

    return [pyval(x) for x in xs]


def _apply_initial_x(initial_x, target_x):
    assert len(initial_x) == len(target_x)
    for i, x in enumerate(initial_x):
        if x is not None:
            target_x[i] = x


def _apply_missing_flag_vals(flag_vals, trials):
    for trial in trials:
        trial.update({name: flag_vals[name] for name in flag_vals if name not in trial})


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
    return (names, [dims[name] for name in names], [initials[name] for name in names])


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
        raise InvalidSearchDimension(
            "unknown function '%s' used for flag %s" % (func_name, flag_name)
        )


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
        raise InvalidSearchDimension(
            "%s requires 2 or 3 args, got %s for flag %s" % (func_name, args, flag_name)
        )


###################################################################
# Sequential trials support
###################################################################


def handle_seq_trials(batch_run, suggest_x_cb):
    if os.getenv("PRINT_TRIALS_CMD") == "1":
        _print_trials_cmd_not_supported_error()
    elif os.getenv("PRINT_TRIALS") == "1":
        _print_trials_not_supported_error()
    elif os.getenv("SAVE_TRIALS"):
        _save_trials_not_supported_error()
    else:
        try:
            _run_seq_trials(batch_run, suggest_x_cb)
        except MissingSearchDimension as e:
            missing_search_dim_error(e.flag_vals)
        except InvalidObjective as e:
            _handle_general_error(e)


def _run_seq_trials(batch_run, suggest_x_cb):
    proto_flag_vals = batch_run.batch_proto.get("flags")
    batch_flag_vals = suggest_opts = batch_run.get("flags")
    max_trials = batch_run.get("max_trials") or DEFAULT_MAX_TRIALS
    names, dims, initial_x = _flag_dims_for_search(proto_flag_vals)
    random_state = batch_run.get("random_seed")
    random_starts = min(batch_flag_vals.get("random-starts") or 0, max_trials)
    objective_spec, objective_scalar, objective_negate = _objective_y_info(batch_run)
    runs_count = 0
    for _ in range(max_trials):
        prev_trials = batch_util.trial_results(batch_run, [objective_scalar])
        x0, y0 = _trials_xy_for_prev_trials(prev_trials, names, objective_negate)
        suggest_random_start = _suggest_random_start(x0, runs_count, random_starts)
        _log_seq_trial(
            suggest_random_start,
            random_starts,
            runs_count,
            x0,
            prev_trials,
            objective_spec,
        )
        suggested_x, random_state = _suggest_x(
            suggest_x_cb, dims, x0, y0, suggest_random_start, random_state, suggest_opts
        )
        if runs_count == 0 and suggested_x:
            _apply_initial_x(initial_x, suggested_x)
        trial_flag_vals = _trial_flags_for_x(suggested_x, names, proto_flag_vals)
        batch_util.run_trial(batch_run, trial_flag_vals)
        runs_count += 1


def _flag_dims_for_search(proto_flag_vals):
    names, dims, initial_x = flag_dims(proto_flag_vals)
    if not names:
        raise MissingSearchDimension(proto_flag_vals)
    return names, dims, initial_x


def _objective_y_info(batch_run):
    objective_spec = batch_run.get("objective") or DEFAULT_OBJECTIVE
    if objective_spec[0] == "-":
        objective_spec = objective_spec[1:]
        y_negate = -1
    else:
        y_negate = 1
    try:
        colspec = qparse.parse_colspec(objective_spec)
    except qparse.ParseError as e:
        raise InvalidObjective("invalid objective %r: %s" % (objective_spec, e))
    else:
        if len(colspec.cols) > 1:
            raise InvalidObjective(
                "invalid objective %r: too many columns" % objective_spec
            )
        col = colspec.cols[0]
        prefix, key = col.split_key()
        y_scalar_col = (prefix, key, col.qualifier)
        return objective_spec, y_scalar_col, y_negate


def _trials_xy_for_prev_trials(prev_trials, names, objective_negate):
    assert names
    x0 = []
    y0 = []
    for flags, y_scalars in prev_trials:
        assert len(y_scalars) == 1
        y = y_scalars[0]
        if y is None:
            continue
        x0.append([flags.get(name) for name in names])
        y0.append(objective_negate * y)
    if not x0:
        return None, None
    return x0, y0


def _suggest_random_start(x0, runs_count, wanted_random_starts):
    return x0 is None or runs_count < wanted_random_starts


def _log_seq_trial(
    suggest_random_start, random_starts, runs_count, x0, prev_trials, objective
):
    """Logs whether trial is random or based on previous trials.

    suggest_random_start is the authoritative flag that indicates
    whether or not a random trial is used. The remaining args are used
    to infer the explanation.

    """
    if suggest_random_start:
        explanation = _random_start_explanation(
            random_starts, runs_count, x0, prev_trials, objective
        )
        log.info("Random start for optimization (%s)", explanation)
    else:
        log.info("Found %i previous trial(s) for use in optimization", len(prev_trials))


def _random_start_explanation(random_starts, runs_count, x0, prev_trials, objective):
    if runs_count < random_starts:
        return "%s of %s" % (runs_count + 1, random_starts)
    elif not prev_trials:
        return "missing previous trials"
    elif not x0:
        return "cannot find objective '%s'" % objective
    else:
        assert False, (random_starts, runs_count, x0, prev_trials, objective)


def _suggest_x(
    suggest_x_cb, dims, x0, y0, suggest_random_start, random_state, suggest_opts
):
    log.debug(
        "suggestion inputs: dims=%s x0=%s y0=%s "
        "random_start=%s random_state=%s opts=%s",
        dims,
        x0,
        y0,
        suggest_random_start,
        random_state,
        suggest_opts,
    )
    return suggest_x_cb(dims, x0, y0, suggest_random_start, random_state, suggest_opts)


def _trial_flags_for_x(x, names, proto_flag_vals):
    flags = dict(proto_flag_vals)
    flags.update(dict(zip(names, _native_python_xs(x))))
    return flags


###################################################################
# Error handlers
###################################################################


def missing_search_dim_error(flag_vals):
    log.error(
        "flags for batch (%s) do not contain any search dimensions\n"
        "Try specifying a range for one or more flags as NAME=[MIN:MAX].",
        op_util.flags_desc(flag_vals),
    )
    raise SystemExit(1)


def _print_trials_cmd_not_supported_error():
    log.error("optimizer does not support printing trials command")
    raise SystemExit(1)


def _print_trials_not_supported_error():
    log.error("optimizer does not support printing trials")
    raise SystemExit(1)


def _save_trials_not_supported_error():
    log.error("optimizer does not support saving trials")
    raise SystemExit(1)


def _handle_general_error(e):
    log.error(e)
    raise SystemExit(1)
