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
from __future__ import print_function

import datetime
import functools
import importlib
import inspect
import logging
import os
import sys
import threading
import warnings

import six

with warnings.catch_warnings():
    warnings.simplefilter("ignore", Warning)
    warnings.filterwarnings("ignore", message="numpy.dtype size changed")
    warnings.filterwarnings("ignore", message="numpy.ufunc size changed")
    try:
        import pandas as pd
    except ImportError:
        raise RuntimeError(
            "guild.ipy requires pandas - install it first before using "
            "this module (see https://pandas.pydata.org/pandas-docs/stable/"
            "install.html for help)"
        )

# ipy makes use of the full Guild API and so, like main_bootstrap,
# requires the external modules.

from guild import main_bootstrap

main_bootstrap.ensure_external_path()

from guild import batch_util
from guild import click_util
from guild import config
from guild import exit_code
from guild import index as indexlib
from guild import model_proxy
from guild import op_util
from guild import opref as opreflib
from guild import run as runlib
from guild import run_util
from guild import summary
from guild import util
from guild import var

from guild.commands import runs_impl

log = logging.getLogger("guild")

RUN_DETAIL = [
    "id",
    "operation",
    "status",
    "started",
    "stopped",
    "label",
    "run_dir",
]

DEFAULT_MAX_TRIALS = 20


class RunException(Exception):
    def __init__(self, run, from_exc):
        super(RunException, self).__init__(run, from_exc)
        self.run = run
        self.from_exc = from_exc


class RunError(RunException):
    pass


class RunTerminated(RunException):
    pass


class OutputTee(object):
    def __init__(self, fs, lock):
        self._fs = fs
        self._lock = lock

    def write(self, s):
        with self._lock:
            for f in self._fs:
                f.write(s)

    def flush(self):
        with self._lock:
            for f in self._fs:
                f.flush()


class RunOutput(object):
    def __init__(self, run, summary=None):
        self.run = run
        self.summary = summary
        self._f = None
        self._f_lock = None
        self._stdout = None
        self._stderr = None

    def __enter__(self):
        self._f = open(self.run.guild_path("output"), "w")
        self._f_lock = threading.Lock()
        self._stdout = sys.stdout
        sys.stdout = OutputTee(self._tee_fs(sys.stdout), self._f_lock)
        self._stderr = sys.stderr
        sys.stderr = OutputTee(self._tee_fs(sys.stderr), self._f_lock)

    def _tee_fs(self, iof):
        fs = [iof, self._f]
        if self.summary:
            fs.append(self.summary)
        return fs

    def __exit__(self, *exc):
        with self._f_lock:
            self._f.close()
        if self.summary:
            self.summary.close()
        sys.stdout = self._stdout
        sys.stderr = self._stderr


@functools.total_ordering
class RunIndex(object):
    def __init__(self, run, fmt):
        self.value = run
        self.run = run  # backward compatible alias
        self.fmt = fmt

    def __str__(self):
        return self.value.short_id

    def __eq__(self, x):
        return self._x_id(x) == self.value.id

    def __lt__(self, x):
        return self.value.id < self._x_id(x)

    @staticmethod
    def _x_id(x):
        if isinstance(x, six.string_types):
            return x
        elif isinstance(x, RunIndex):
            return x.value.id
        return None


class RunsSeries(pd.Series):
    @property
    def _constructor(self):
        return RunsSeries

    @property
    def _constructor_expanddim(self):
        return RunsDataFrame

    def delete(self, **kw):
        self.to_frame().delete(**kw)

    def info(self, **kw):
        _print_run_info(self[0], **kw)

    def scalars(self):
        return _runs_scalars([self[0].value])

    def scalars_detail(self):
        return _runs_scalars_detail([self[0].value])

    def flags(self):
        return _runs_flags([self[0].value])

    def compare(self):
        return _runs_compare([self[0]])


class RunsDataFrame(pd.DataFrame):
    @property
    def _constructor(self):
        return RunsDataFrame

    @property
    def _constructor_sliced(self):
        return RunsSeries

    @property
    def _constructor_expanddim(self):
        return RunsDataFrame

    def delete(self, permanent=False):
        runs = self._runs()
        var.delete_runs(runs, permanent)
        return [run.id for run in runs]

    def _runs(self):
        return [row[1][0].value for row in self.iterrows()]

    def _items(self):
        return [row[1][0] for row in self.iterrows()]

    # pylint: disable=arguments-differ
    def info(self, *args, **kw):
        self.loc[0].info(*args, **kw)

    def scalars(self):
        return _runs_scalars(self._runs())

    def scalars_detail(self):
        return _runs_scalars_detail(self._runs())

    def flags(self):
        return _runs_flags(self._runs())

    def compare(self):
        return _runs_compare(self._items())


class Batch(object):
    def __init__(self, gen_trials, op, flag_vals, opts):
        self.gen_trials = gen_trials
        self.op = op
        self.flag_vals = _coerce_range_functions(flag_vals)
        self.opts = opts

    def __call__(self):
        runs = []
        results = []
        prev_results_cb = lambda: (runs, results)
        for trial in self.gen_trials(self.flag_vals, prev_results_cb, **self.opts):
            trial_flag_vals, trial_attrs = _split_gen_trial(trial)
            print(
                "Running %s (%s):"
                % (self.op.__name__, op_util.flags_desc(trial_flag_vals))
            )
            run, result = _run(self.op, trial_flag_vals, self.opts, trial_attrs)
            runs.append(run)
            results.append(result)
        return runs, results


def _split_gen_trial(trial):
    if isinstance(trial, tuple):
        assert len(trial) == 2, ("generated trial must be a two-tuple or a dict", trial)
        return trial
    else:
        return trial, {}


def _coerce_range_functions(flag_vals):
    return {name: _coerce_range_function(val) for name, val in flag_vals.items()}


def _coerce_range_function(val):
    if isinstance(val, RangeFunction):
        return str(val)
    return val


class RangeFunction(object):
    def __init__(self, name, *args):
        self.name = name
        self.args = args

    def __str__(self):
        args = ":".join([str(arg) for arg in self.args])
        return "%s[%s]" % (self.name, args)


def batch_gen_trials(flag_vals, _prev_trials_cb, max_trials=None, **kw):
    if kw:
        log.warning("ignoring batch config: %s", kw)
    max_trials = max_trials or DEFAULT_MAX_TRIALS
    trials = 0
    for trial_flag_vals in batch_util.expand_flags(flag_vals):
        if trials >= max_trials:
            return
        trials += 1
        yield trial_flag_vals


def optimizer_trial_generator(model_op):
    main_mod = _optimizer_module(model_op.module_name)
    try:
        return main_mod.gen_trials
    except AttributeError:
        raise TypeError(
            "%s optimizer module does not implement gen_trials" % main_mod.__name__
        )


def _optimizer_module(module_name):
    return importlib.import_module(module_name)


def uniform(low, high):
    return RangeFunction("uniform", low, high)


def loguniform(low, high):
    return RangeFunction("loguniform", low, high)


def run(op, *args, **kw):
    if not callable(op):
        raise ValueError("op must be callable")
    opts = _pop_opts(kw)
    flag_vals = _init_flag_vals(op, args, kw)
    run = _init_runner(op, flag_vals, opts)
    return run()


def _pop_opts(kw):
    opts = {}
    for name in list(kw):
        if name[:1] == "_":
            opts[name[1:]] = kw.pop(name)
    return opts


def _init_flag_vals(op, args, kw):
    # pylint: disable=deprecated-method
    op_f = _op_f(op)
    op_flag_vals = inspect.getcallargs(op_f, *args, **kw)
    _remove_bound_method_self(op_f, op_flag_vals)
    return _coerce_slice_vals(op_flag_vals)


def _op_f(op):
    assert callable(op), repr(op)
    if inspect.isfunction(op) or inspect.ismethod(op):
        return op
    assert hasattr(op, "__call__")
    return op.__call__


def _remove_bound_method_self(op, op_flag_vals):
    im_self = util.find_apply(
        [
            lambda: getattr(op, "__self__", None),
            lambda: getattr(op, "im_self", None),
        ]
    )
    if im_self:
        for key, val in op_flag_vals.items():
            if val is im_self:
                del op_flag_vals[key]
                break
        else:
            assert False, (op_flag_vals, im_self)


def _coerce_slice_vals(flag_vals):
    return {name: _coerce_slice_val(val) for name, val in flag_vals.items()}


def _coerce_slice_val(val):
    if isinstance(val, slice):
        return uniform(val.start, val.stop)
    return val


def _init_runner(op, flag_vals, opts):
    return util.find_apply(
        [_optimize_runner, _batch_runner, _single_runner], op, flag_vals, opts
    )


def _optimize_runner(op, flag_vals, opts):
    optimizer = opts.get("optimizer")
    if not optimizer:
        return _maybe_random_runner(op, flag_vals, opts)
    opts = _filter_kw(opts, ["optimizer"])
    return Batch(_init_gen_trials(optimizer), op, flag_vals, opts)


def _filter_kw(opts, keys):
    return {k: v for k, v in opts.items() if k not in keys}


def _maybe_random_runner(op, flag_vals, opts):
    assert not opts.get("optimizer"), opts
    for val in flag_vals.values():
        if isinstance(val, RangeFunction):
            return Batch(_init_gen_trials("random"), op, flag_vals, opts)
    return None


def _init_gen_trials(optimizer):
    try:
        model_op, _name = model_proxy.resolve_plugin_model_op(optimizer)
    except model_proxy.NotSupported:
        raise TypeError("optimizer %r is not supported" % optimizer)
    else:
        return optimizer_trial_generator(model_op)


def _batch_runner(op, flag_vals, opts):
    for val in flag_vals.values():
        if isinstance(val, list):
            return Batch(batch_gen_trials, op, flag_vals, opts)
    return None


def _single_runner(op, flag_vals, opts):
    return lambda: _run(op, flag_vals, opts)


def _run(op, flag_vals, opts, extra_attrs=None):
    run = _init_run()
    _init_run_attrs(run, op, flag_vals, opts, extra_attrs)
    summary = _init_output_scalars(run, opts)
    try:
        with RunOutput(run, summary):
            _write_proc_lock(run)
            with util.Chdir(run.path):
                result = op(**flag_vals)
    except KeyboardInterrupt as e:
        exit_status = exit_code.SIGTERM
        util.raise_from(RunTerminated(run, e), e)
    except Exception as e:
        exit_status = exit_code.DEFAULT_ERROR
        util.raise_from(RunError(run, e), e)
    else:
        exit_status = 0
        return run, result
    finally:
        _finalize_run(run, exit_status)


def _init_run():
    run_id = runlib.mkid()
    run_dir = os.path.join(var.runs_dir(), run_id)
    run = runlib.Run(run_id, run_dir)
    run.init_skel()
    return run


def _init_run_attrs(run, op, flag_vals, opts, extra_attrs):
    opref = opreflib.OpRef("func", "", "", "", _op_name(op, opts))
    run.write_opref(opref)
    run.write_attr("started", runlib.timestamp())
    run.write_attr("flags", flag_vals)
    run.write_attr("label", _run_label(flag_vals, opts))
    if extra_attrs:
        for name, val in extra_attrs.items():
            run.write_attr(name, val)


def _op_name(op, opts):
    return opts.get("op_name") or _default_op_name(op)


def _default_op_name(op):
    if inspect.isfunction(op) or inspect.ismethod(op):
        return op.__name__
    return op.__class__.__name__


def _run_label(flag_vals, opts):
    return op_util.run_label(_label_template(opts), flag_vals)


def _label_template(opts):
    return util.find_apply([_explicit_label, _tagged_label], opts)


def _explicit_label(opts):
    return opts.get("label")


def _tagged_label(opts):
    try:
        tag = opts["tag"]
    except KeyError:
        return None
    else:
        return "%s ${default_label}" % tag


def _init_output_scalars(run, opts):
    config = opts.get("output_scalars", summary.DEFAULT_OUTPUT_SCALARS)
    if not config:
        return None
    abs_guild_path = os.path.abspath(run.guild_path())
    return summary.OutputScalars(config, abs_guild_path)


def _write_proc_lock(run):
    op_util.write_proc_lock(os.getpid(), run)


def _finalize_run(run, exit_status):
    run.write_attr("exit_status", exit_status)
    run.write_attr("stopped", runlib.timestamp())
    op_util.delete_proc_lock(run)


def runs(**kw):
    runs = runs_impl.filtered_runs(_runs_cmd_args(**kw))
    data, cols = _format_runs(runs)
    return RunsDataFrame(data=data, columns=cols)


def _runs_cmd_args(
    operations=None,
    labels=None,
    tags=None,
    comments=None,
    running=False,
    completed=False,
    error=False,
    terminated=False,
    pending=False,
    staged=False,
    unlabeled=None,
    marked=False,
    unmarked=False,
    started=None,
    digest=None,
    deleted=None,
    remote=None,
):
    operations = operations or ()
    labels = labels or ()
    tags = tags or ()
    comments = comments or ()
    return click_util.Args(
        filter_ops=operations,
        filter_labels=labels,
        filter_tags=tags,
        filter_comments=comments,
        status_running=running,
        status_completed=completed,
        status_error=error,
        status_terminated=terminated,
        status_pending=pending,
        status_staged=staged,
        filter_unlabeled=unlabeled,
        filter_marked=marked,
        filter_unmarked=unmarked,
        filter_started=started,
        filter_digest=digest,
        deleted=deleted,
        remote=remote,
    )


def _format_runs(runs):
    cols = (
        "run",
        "operation",
        "started",
        "status",
        "label",
    )
    data = [_format_run(run, cols) for run in runs]
    return data, cols


def _format_run(run, cols):
    fmt = run_util.format_run(run)
    return [_run_attr(run, name, fmt) for name in cols]


def _run_attr(run, name, fmt):
    if name == "run":
        return RunIndex(run, fmt)
    elif name in ("operation",):
        return fmt[name]
    elif name in ("started", "stopped"):
        return _datetime(run.get(name))
    elif name in ("label",):
        return run.get(name, "")
    elif name == "time":
        return _run_time(run)
    else:
        return getattr(run, name)


def _datetime(ts):
    if ts is None:
        return None
    return datetime.datetime.fromtimestamp(int(ts / 1000000))


def _run_time(run):
    formatted_time = util.format_duration(run.get("started"), run.get("stopped"))
    return pd.to_timedelta(formatted_time)


def _print_run_info(item, output=False, scalars=False):
    for name in RUN_DETAIL:
        print("%s: %s" % (name, item.fmt.get(name, "")))
    print("flags:", end="")
    print(run_util.format_attr(item.value.get("flags", "")))
    if scalars:
        print("scalars:")
        for s in indexlib.iter_run_scalars(item.value):
            print("  %s: %f (step %i)" % (s["tag"], s["last_val"], s["last_step"]))
    if output:
        print("output:")
        for line in run_util.iter_output(item.value):
            print("  %s" % line, end="")


def _runs_scalars(runs):
    data = []
    cols = [
        "run",
        "prefix",
        "tag",
        "first_val",
        "first_step",
        "last_val",
        "last_step",
        "min_val",
        "min_step",
        "max_val",
        "max_step",
        "avg_val",
        "count",
        "total",
    ]
    for run in runs:
        for s in indexlib.iter_run_scalars(run):
            data.append(s)
    return pd.DataFrame(data, columns=cols)


def _runs_scalars_detail(runs):
    from guild import tfevent

    data = []
    cols = [
        "run",
        "path",
        "tag",
        "val",
        "step",
    ]
    for run in runs:
        for path, _run_id, scalars in tfevent.scalar_readers(run.dir):
            rel_path = os.path.relpath(path, run.dir)
            for tag, val, step in scalars:
                data.append([run, rel_path, tag, val, step])
    return pd.DataFrame(data, columns=cols)


def _runs_flags(runs):
    data = [_run_flags_data(run) for run in runs]
    return pd.DataFrame(data)


def _run_flags_data(run):
    data = run.get("flags") or {}
    data[_run_flags_key(data)] = run.id
    return data


def _run_flags_key(flag_vals):
    run_key = "run"
    while run_key in flag_vals:
        run_key = "_" + run_key
    return run_key


def _runs_compare(items):
    core_cols = ["run", "operation", "started", "time", "status", "label"]
    flag_cols = set()
    scalar_cols = set()
    data = []
    for item in items:
        row_data = {}
        data.append(row_data)
        # Order matters here - we want flag vals to take precedence
        # over scalar vals with the same name.
        _apply_scalar_data(item.value, scalar_cols, row_data)
        _apply_flag_data(item.value, flag_cols, row_data)
        _apply_run_core_data(item, core_cols, row_data)
    cols = core_cols + sorted(flag_cols) + _sort_scalar_cols(scalar_cols, flag_cols)
    return pd.DataFrame(data, columns=cols)


def _apply_scalar_data(run, cols, data):
    for name, val in _run_scalar_data(run).items():
        cols.add(name)
        data[name] = val


def _run_scalar_data(run):
    data = {}
    step = None
    last_step = None
    for s in indexlib.iter_run_scalars(run):
        key = s["tag"]
        data[key] = s["last_val"]
        last_step = s["last_step"]
        if key == "loss":
            step = last_step
    if data:
        if step is None:
            step = last_step
        data["step"] = step
    return data


def _apply_flag_data(run, cols, data):
    for name, val in _run_flags_data(run).items():
        if name == "run":
            continue
        cols.add(name)
        data[name] = val


def _apply_run_core_data(item, cols, data):
    for name in cols:
        data[name] = _run_attr(item.value, name, item.fmt)


def _sort_scalar_cols(scalar_cols, flag_cols):
    # - List step first if it exists
    # - Don't include flag cols in result
    cols = []
    if "step" in scalar_cols:
        cols.append("step")
    for col in sorted(scalar_cols):
        if col == "step" or col in flag_cols:
            continue
        cols.append(col)
    return cols


def guild_home():
    return config.guild_home()


def set_guild_home(path):
    config.set_guild_home(path)
