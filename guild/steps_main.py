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
import re
import subprocess
import sys

import click
import six

import guild.log

from guild import exit_code
from guild import flag_util
from guild import op_util
from guild import opref as opreflib
from guild import run as runlib
from guild import run_check
from guild import util

log = None  # intialized in _init_logging

STEP_USED_PARAMS = (
    "flags",
    "gpus",
    "label",
    "max_trials",
    "needed",
    "no_gpus",
    "opspec",
    "opt_flags",
    "optimizer",
    "random_seed",
    "stop_after",
    "tag",
)

###################################################################
# State
###################################################################


class Step(object):
    def __init__(self, data, parent_flags, parent_opref, parent_run_params):
        data = _coerce_step_data(data)
        params = _run_params_for_step_data(data)
        _apply_parent_run_params(parent_run_params, params)
        assert params["opspec"], params
        opspec_param = params["opspec"]
        self.op_spec = _apply_default_model(opspec_param, parent_opref)
        self.name = data.get("name") or opspec_param
        self.batch_files, flag_args = _split_batch_files(params["flags"])
        self.flags = _init_step_flags(flag_args, parent_flags, self)
        self.checks = _init_checks(data)
        self.isolate_runs = bool(data.get("isolate-runs", True))
        self.label = _resolve_param(params, "label", parent_flags)
        self.tag = _resolve_param(params, "tag", parent_flags)
        self.gpus = _resolve_param(params, "gpus", parent_flags)
        self.no_gpus = params["no_gpus"]
        self.stop_after = params["stop_after"]
        self.needed = params["needed"]
        self.optimizer = params["optimizer"]
        self.opt_flags = params["opt_flags"]
        self.max_trials = params["max_trials"]
        self.random_seed = params["random_seed"]

    def __str__(self):
        return self.name or self.op_spec


def _coerce_step_data(data):
    if isinstance(data, six.string_types):
        data = {"run": data}
    elif isinstance(data, dict):
        data = dict(data)
    else:
        _error("invalid step data: %r" % data)
    if "flags" in data:
        data["flags"] = _coerce_flags_data(data["flags"])
    return data


def _coerce_flags_data(data):
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return flag_util.format_flag_assigns(data)
    else:
        _error("invalid flags value %r" % data)


def _run_params_for_step_data(data):
    from guild.commands.run import run as run_cmd

    run_spec = data.get("run", "").strip()
    if not run_spec:
        _error("invalid step %r: must define run" % data)
    args = util.shlex_split(run_spec)
    try:
        ctx = run_cmd.make_context("run", args)
    except click.exceptions.ClickException as e:
        _error("invalid run spec %r: %s" % (run_spec, e))
    else:
        _apply_data_params(data, ctx, run_spec)
        return ctx.params


def _apply_data_params(data, ctx, run_spec):
    """Apply applicable data to params.

    Warns if params contains unused values.
    """
    defaults = {p.name: p.default for p in ctx.command.params}
    for name, val in sorted(ctx.params.items()):
        if name in STEP_USED_PARAMS:
            data_name = name.replace("_", "-")
            try:
                data_val = data[data_name]
            except KeyError:
                pass
            else:
                if data_val != defaults[name]:
                    ctx.params[name] = data_val
        else:
            if val != defaults[name]:
                log.warning("run parameter %s used in %r ignored", name, run_spec)


def _apply_parent_run_params(parent_params, target_params):
    """Applies parent run params to target params.

    A parent param is applied if it isn't defined in target.
    """
    for name in parent_params:
        if target_params.get(name) is None:
            target_params[name] = parent_params[name]


def _init_step_flags(flag_args, parent_flag_vals, step):
    flag_vals = _parse_flag_assigns(flag_args)
    _apply_parent_flags(parent_flag_vals, step, flag_vals)
    resolved = _resolve_flag_vals(flag_vals, parent_flag_vals)
    return _remove_undefined_flags(resolved)


def _parse_flag_assigns(assigns):
    assert isinstance(assigns, list), assigns
    try:
        return op_util.parse_flag_assigns(assigns)
    except op_util.ArgValueError as e:
        _error("invalid argument '%s' - expected NAME=VAL" % e.arg)


def _apply_parent_flags(parent_flag_vals, step, flag_vals):
    prefixes = [
        step.op_spec + ":",
        step.name + ":",
    ]
    flag_vals.update(_prefixed_flag_vals(prefixes, parent_flag_vals))


def _prefixed_flag_vals(prefixes, flag_vals):
    """Returns a dict of prefixed flag values.

    Prefixes are stripped from matching flag names.

    The value for the first matching prefix from prefixes is used.
    """
    prefixed = {}
    for prefix in prefixes:
        for full_name in flag_vals:
            if full_name.startswith(prefix):
                prefixed_name = full_name[len(prefix) :]
                prefixed.setdefault(prefixed_name, flag_vals[full_name])
    return prefixed


def _apply_default_model(step_opspec, parent_opref):
    step_opref = opreflib.OpRef.for_string(step_opspec)
    if not step_opref.model_name:
        step_opref = opreflib.OpRef(
            step_opref.pkg_type,
            step_opref.pkg_name,
            step_opref.pkg_version,
            parent_opref.model_name,
            step_opref.op_name,
        )
    return step_opref.to_opspec()


def _split_batch_files(flag_args):
    return op_util.split_batch_files(flag_args)


def _resolve_flag_vals(flags, parent_flags):
    return {name: util.resolve_refs(val, parent_flags) for name, val in flags.items()}


def _remove_undefined_flags(flag_vals):
    return {name: val for name, val in flag_vals.items() if val is not None}


def _resolve_param(params, name, flags):
    resolved = util.resolve_refs(params[name], flags)
    if resolved is None:
        return resolved
    return str(resolved)


def _init_checks(data):
    expect = data.get("expect") or []
    if not isinstance(expect, list):
        expect = [expect]
    checks = []
    for check_data in expect:
        try:
            check = run_check.init_check(check_data)
        except ValueError as e:
            log.warning("invalid check %r: %e", data, e)
        else:
            checks.append(check)
    return checks


###################################################################
# Main
###################################################################


def main():
    _init_logging()
    _run_steps()


def _init_logging():
    level = int(os.getenv("LOG_LEVEL", logging.WARN))
    format = os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    guild.log.init_logging(level, {"_": format})
    globals()["log"] = logging.getLogger("guild")


def _run_steps():
    run = _init_run()
    steps = _init_steps(run)
    if not steps:
        log.warning("no steps defined for run %s", run.id)
        return
    for step in steps:
        step_run = _run_step(step, run)
        _maybe_check_step_run(step, step_run)


# =================================================================
# Init
# =================================================================


def _init_run():
    run_id, run_dir = _run_environ()
    return runlib.Run(run_id, run_dir)


def _run_environ():
    try:
        return os.environ["RUN_ID"], os.environ["RUN_DIR"]
    except KeyError as e:
        _internal_error("missing required env %s" % e.args[0])


def _init_steps(run):
    data = run.get("steps")
    if not data:
        return []
    if not isinstance(data, list):
        _error("invalid steps data %r: expected list" % data)
    flags = run.get("flags")
    opref = run.opref
    params = run.get("run_params") or {}
    return [Step(step_data, flags, opref, params) for step_data in data]


# =================================================================
# Run step
# =================================================================


def _run_step(step, parent_run):
    step_run = _init_step_run(parent_run)
    cmd = _init_step_cmd(step, step_run.path)
    _link_to_step_run(step, step_run.path, parent_run.path)
    env = dict(os.environ)
    env["NO_WARN_RUNDIR"] = "1"
    if step.isolate_runs:
        env["GUILD_RUNS_PARENT"] = parent_run.id
    cwd = os.getenv("CMD_DIR")
    log.info("running %s: %s", step, _format_step_cmd(cmd))
    log.debug("step cwd %s", cwd)
    log.debug("step command: %s", cmd)
    log.debug("step env: %s", env)
    returncode = subprocess.call(cmd, env=env, cwd=cwd)
    if returncode != 0:
        sys.exit(returncode)
    return step_run


def _init_step_run(parent_run):
    """Returns the run dir for a step run.

    Directory is based on a new, unique run ID but is not created.
    """
    runs_dir = os.path.dirname(parent_run.path)
    step_run_id = runlib.mkid()
    step_run_dir = os.path.join(runs_dir, step_run_id)
    return runlib.Run(step_run_id, step_run_dir)


def _init_step_cmd(step, step_run_dir):
    base_args = [
        sys.executable,
        "-um",
        "guild.main_bootstrap",
        "run",
        "-y",
        "--force-flags",
        "--run-dir",
        step_run_dir,
        step.op_spec,
    ]
    step_options = _step_options(step)
    batch_file_args = _step_batch_file_args(step)
    flag_args = _step_flag_args(step)
    return base_args + step_options + batch_file_args + flag_args


def _step_options(step):
    opts = []
    if step.label:
        opts.extend(["--label", step.label])
    if step.gpus is not None:
        opts.extend(["--gpus", step.gpus])
    elif step.no_gpus:
        opts.append("--no-gpus")
    if step.stop_after:
        opts.extend(["--stop-after", str(step.stop_after)])
    if step.needed:
        opts.append("--needed")
    if step.optimizer:
        opts.extend(["--optimizer", step.optimizer])
    for flag in step.opt_flags:
        opts.extend(["--opt-flag", flag])
    if step.max_trials:
        opts.extend(["--max-trials", str(step.max_trials)])
    if step.random_seed is not None:
        opts.extend(["--random-seed", str(step.random_seed)])
    if step.tag:
        opts.extend(["--tag", step.tag])
    return opts


def _step_batch_file_args(step):
    return ["@%s" % file for file in step.batch_files]


def _step_flag_args(step):
    return flag_util.format_flag_assigns(step.flags)


def _link_to_step_run(step, step_run_dir, parent_run_dir):
    link_name = _step_link_name(step)
    link_path_base = os.path.join(parent_run_dir, link_name)
    link_path = _ensure_unique_link(link_path_base)
    os.symlink(step_run_dir, link_path)


def _step_link_name(step):
    return re.sub(r"[ :/\\]", "_", str(step))


def _ensure_unique_link(path_base):
    v = 2
    path = path_base
    while True:
        assert v < 1e6
        if not os.path.lexists(path):
            return path
        path = "%s_%i" % (path_base, v)
        v += 1


def _format_step_cmd(cmd):
    # Show only opspec onward - assert front matter to catch changes
    # to cmd.
    assert cmd[0:7] == [
        sys.executable,
        "-um",
        "guild.main_bootstrap",
        "run",
        "-y",
        "--force-flags",
        "--run-dir",
    ], cmd
    return " ".join([arg for arg in cmd[8:]])


def _maybe_check_step_run(step, run):
    if not step.checks:
        return
    if _run_skipped(run):
        log.info("skipping checks for %s", step.name)
        return
    checks_passed = _check_step_run(step, run)
    if not checks_passed:
        _error("stopping because a check failed", exit_code.TEST_FAILED)


def _run_skipped(run):
    """Returns True if run was skipped.

    We infer that a run was skipped if it's directory doesn't
    exist. The rationale relies on the assertion that the step run
    creates the specified run directory only when the run is not
    skipped.
    """
    return not os.path.exists(run.path)


def _check_step_run(step, run):
    if not step.checks:
        return True
    passed = 0
    failed = 0
    for check in step.checks:
        try:
            check.check_run(run)
        except run_check.Failed as e:
            log.error("check failed: %s", e)
            failed += 1
        else:
            passed += 1
    log.info("%i of %i checks passed", passed, passed + failed)
    if failed > 0:
        log.error("%i check(s) failed - see above for details", failed)
    return failed == 0


###################################################################
# Error messages
###################################################################


def _internal_error(msg):
    sys.stderr.write("guild.steps_main: %s\n" % msg)
    sys.exit(exit_code.INTERNAL_ERROR)


def _error(msg, exit_code=exit_code.DEFAULT_ERROR):
    sys.stderr.write("guild: %s\n" % msg)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
