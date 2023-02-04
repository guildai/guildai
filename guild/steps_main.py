# Copyright 2017-2022 RStudio, PBC
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

import logging
import os
import subprocess
import sys
import typing

import click

import guild.log

from guild import config
from guild import exit_code
from guild import flag_util
from guild import op_util
from guild import opref as opreflib
from guild import steps_util
from guild import run_check
from guild import util

log = None  # intialized in _init_logging

STEP_USED_PARAMS = (
    "additional_deps",
    "batch_label",
    "batch_tags",
    "break_",
    "break_on_error",
    "fail_on_trial_error",
    "flags",
    "force_flags",
    "gpus",
    "label",
    "max_trials",
    "maximize",
    "minimize",
    "needed",
    "no_gpus",
    "opspec",
    "opt_flags",
    "optimize",
    "optimizer",
    "random_seed",
    "remote",
    "stop_after",
    "tags",
)

# List of batch params that a trial inherits if unset for trial.
INHERITED_PARAMS = (
    # (param_name, unset_val)
    ("label", None),
    ("tags", ()),
)

###################################################################
# State
###################################################################


class Step:
    def __init__(self, data, parent_flags, parent_opref, parent_run_params):
        data = _coerce_step_data(data)
        params = _run_params_for_step_data(data)
        _apply_batch_params_to_trial(parent_run_params, params)
        assert params["opspec"], params
        opspec_param = params["opspec"]
        self.op_spec = _apply_default_model(opspec_param, parent_opref)
        self.name = data.get("name") or opspec_param
        self.batch_files, flag_args = _split_batch_files(params["flags"])
        self.checks = _init_checks(data)
        self.isolate_runs = bool(data.get("isolate-runs", True))
        # Standard run params
        self.batch_label = params["batch_label"]
        self.batch_tags = params["batch_tags"]
        self.fail_on_trial_error = params["fail_on_trial_error"]
        self.flags = _init_step_flags(flag_args, parent_flags, self)
        self.force_flags = params["force_flags"]
        self.gpus = _resolve_refs(params["gpus"], parent_flags)
        self.label = _resolve_refs(params["label"], parent_flags)
        self.max_trials = params["max_trials"]
        self.maximize = params["maximize"]
        self.minimize = params["minimize"]
        self.needed = params["needed"]
        self.no_gpus = params["no_gpus"]
        self.opt_flags = params["opt_flags"]
        self.optimize = params["optimize"]
        self.optimizer = params["optimizer"]
        self.random_seed = params["random_seed"]
        self.remote = params["remote"]
        self.stop_after = params["stop_after"]
        self.tags = [_resolve_refs(tag, parent_flags) for tag in params["tags"]]

    def __str__(self):
        return self.name or self.op_spec


def _coerce_step_data(data):
    if isinstance(data, str):
        data = {"run": data}
    elif isinstance(data, dict):
        data = dict(data)
    else:
        _error(f"invalid step data: {data!r}")
    if "flags" in data:
        data["flags"] = _coerce_flags_data(data["flags"])
    return data


def _coerce_flags_data(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return flag_util.flag_assigns(data)
    _error(f"invalid flags value {data!r}")


def _run_params_for_step_data(data):
    from guild.commands.run import run as run_cmd

    run_spec = data.get("run", "").strip()
    if not run_spec:
        _error(f"invalid step {data!r}: must define run")
    args = util.shlex_split(run_spec)
    try:
        ctx = run_cmd.make_context("run", args)
    except click.exceptions.ClickException as e:
        _error(f"invalid run spec {run_spec!r}: {e}")
    else:
        _apply_data_params(data, ctx, run_spec)
        return ctx.params


def _apply_data_params(data, ctx, run_spec):
    """Apply applicable data to ctx.params.

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


def _apply_batch_params_to_trial(batch_params, trial_params):
    """Applies batch params to trial params.

    The list of parent params that are applied is defined by INHERITED_PARAMS.
    """
    for name, unset_val in INHERITED_PARAMS:
        if name in batch_params and trial_params.get(name) == unset_val:
            trial_params[name] = batch_params[name]


def _init_step_flags(flag_args, parent_flag_vals, step):
    flag_vals, _errors = _parse_flag_assigns(flag_args)
    _apply_parent_flags(parent_flag_vals, step, flag_vals)
    resolved = _resolve_flag_vals(flag_vals, parent_flag_vals)
    return _remove_undefined_flags(resolved)


def _parse_flag_assigns(assigns):
    assert isinstance(assigns, list), assigns
    assigns, errors = op_util.parse_flag_assigns(assigns)
    if errors:
        _error(
            "invalid argument(s):\n%s\nexpected NAME=VAL"
            % "\n".join(e.arg for e in errors.values())
        )
    return assigns, errors


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


def _resolve_refs(val, flags):
    resolved = util.resolve_refs(val, flags)
    if resolved is None:
        return None
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
    level = util.get_env("LOG_LEVEL", int, logging.WARN)
    format = os.getenv("LOG_FORMAT", "%(levelname)s: [%(name)s] %(message)s")
    guild.log.init_logging(level, {"_": format})
    globals()["log"] = logging.getLogger("guild")


def _run_steps():
    parent_run = op_util.current_run()
    steps = _init_steps(parent_run)
    if not steps:
        log.warning("no steps defined for run %s", parent_run.id)
        return
    for step in steps:
        step_run = _run_step(step, parent_run)
        _check_step_run(step, step_run)


def _init_steps(run):
    data = run.get("steps")
    if not data:
        return []
    if not isinstance(data, list):
        _error(f"invalid steps data {data!r}: expected list")
    flags = run.get("flags")
    opref = run.opref
    params = run.get("run_params") or {}
    return [Step(step_data, flags, opref, params) for step_data in data]


# =================================================================
# Run step
# =================================================================


def _run_step(step, parent_run):
    step_run = steps_util.init_step_run(parent_run.dir)
    steps_util.link_to_step_run(step, step_run.dir, parent_run.dir)
    cmd = _step_run_cmd(step, step_run.dir, parent_run)
    env = _step_run_env(step, parent_run)
    cwd = _step_run_cwd()
    log.info("running %s: %s", step, _format_step_cmd(cmd))
    log.debug("step cwd %s", cwd)
    log.debug("step command: %s", cmd)
    log.debug("step env: %s", env)
    returncode = subprocess.call(cmd, env=env, cwd=cwd)
    if returncode != 0:
        sys.exit(returncode)
    return step_run


def _step_run_cmd(step, step_run_dir, parent_run):
    base_args = [
        config.python_exe(),
        "-um",
        "guild.main_bootstrap",
        "run",
        "-y",
        "--run-dir",
        step_run_dir,
        step.op_spec,
    ]
    parent_run_options = _parent_run_options(parent_run)
    step_options = _step_options(step)
    batch_file_args = _step_batch_file_args(step)
    flag_args = _step_flag_args(step)
    return base_args + parent_run_options + step_options + batch_file_args + flag_args


def _parent_run_options(parent_run):
    opts = []
    params = parent_run.get("run_params")
    if params.get("stage_trials"):
        opts.append("--stage-trials")
    return opts


def _step_options(step):
    opts = []
    if step.batch_label:
        opts.extend(["--batch-label", step.batch_label])
    for tag in step.batch_tags:
        opts.extend(["--batch-tag", tag])
    if step.fail_on_trial_error:
        opts.append("--fail-on-trial-error")
    if step.force_flags:
        opts.append("--force-flags")
    if step.gpus is not None:
        opts.extend(["--gpus", str(step.gpus)])
    if step.label:
        opts.extend(["--label", step.label])
    if step.max_trials:
        opts.extend(["--max-trials", str(step.max_trials)])
    if step.maximize:
        opts.extend(["--maximize", step.maximize])
    if step.minimize:
        opts.extend(["--minimize", step.minimize])
    if step.needed:
        opts.append("--needed")
    if step.no_gpus:
        opts.append("--no-gpus")
    for flag in step.opt_flags:
        opts.extend(["--opt-flag", flag])
    if step.optimize:
        opts.append("--optimize")
    if step.optimizer:
        opts.extend(["--optimizer", step.optimizer])
    if step.random_seed is not None:
        opts.extend(["--random-seed", str(step.random_seed)])
    if step.remote:
        opts.extend(["--remote", step.remote])
    if step.stop_after:
        opts.extend(["--stop-after", str(step.stop_after)])
    for tag in step.tags:
        opts.extend(["--tag", tag])
    return opts


def _step_batch_file_args(step):
    return [f"@{file}" for file in step.batch_files]


def _step_flag_args(step):
    return flag_util.flag_assigns(step.flags)


def _step_run_env(step, parent_run):
    env = dict(os.environ)
    env["NO_WARN_RUNDIR"] = "1"
    if step.isolate_runs:
        env["GUILD_RUNS_PARENT"] = parent_run.id
    return env


def _step_run_cwd():
    # We're running from parent dir.
    return os.getenv("PROJECT_DIR") or os.getenv("CMD_DIR")


def _format_step_cmd(cmd):
    # Show only opspec onward - assert front matter to catch changes
    # to cmd.
    assert cmd[0:6] == [
        config.python_exe(),
        "-um",
        "guild.main_bootstrap",
        "run",
        "-y",
        "--run-dir",
    ], cmd
    return " ".join(cmd[7:])


def _check_step_run(step, run):
    if not step.checks:
        return
    if _run_skipped(run):
        log.info("skipping checks for %s", step.name)
        return
    checks_passed = _check_step_run_(step, run)
    if not checks_passed:
        _error("stopping because a check failed", exit_code.TEST_FAILED)


def _run_skipped(run):
    """Returns True if run was skipped.

    We infer that a run was skipped if it's directory doesn't
    exist. The rationale relies on the assertion that the step run
    creates the specified run directory only when the run is not
    skipped.
    """
    return not os.path.exists(run.dir)


def _check_step_run_(step, run):
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
    sys.stderr.write(f"guild.steps_main: {msg}\n")
    sys.exit(exit_code.INTERNAL_ERROR)


def _error(msg, exit_code=exit_code.DEFAULT_ERROR) -> typing.NoReturn:
    sys.stderr.write(f"guild: {msg}\n")
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        op_util.handle_system_exit(e)
