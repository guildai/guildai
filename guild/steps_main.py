# Copyright 2017-2023 Posit Software, PBC
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
from guild import run as runlib
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
        return _coerce_step_str(data)
    if isinstance(data, dict):
        return _coerce_step_dict(data)
    _error(f"invalid step data: {data!r}")


def _coerce_step_str(step_str):
    return {"run": step_str}


def _coerce_step_dict(data0):
    data = dict(data0)
    _maybe_apply_step_flags(data)
    return data


def _maybe_apply_step_flags(data):
    try:
        flags_data = data["flags"]
    except KeyError:
        pass
    else:
        data["flags"] = _coerce_flags_data(flags_data)


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
    for step, step_name in _iter_steps_with_names(steps):
        _handle_run_step(parent_run, step, step_name)


def _iter_steps_with_names(steps):
    unique_step_names = _unique_step_names(steps)
    return zip(steps, unique_step_names)


def _unique_step_names(steps):
    from collections import Counter

    names_counter = Counter()
    unique_step_names = []
    for step in steps:
        unique_step_names.append(
            _step_name_for_count(step.name, names_counter[step.name])
        )
        names_counter[step.name] += 1
    return unique_step_names


def _step_name_for_count(step_name, count):
    return step_name if count == 0 else f"{step_name}_{count + 1}"


def _handle_run_step(parent_run, step, step_name):
    step_run_dir = _resolve_step_run_dir(parent_run, step_name)
    _run_step(step, parent_run, step_run_dir)
    _run_step_checks(step, step_run_dir)


# def _ensure_step_run_dir(parent_run, step, step_name):
#     if _step_run_exists(parent_run, step_name):
#         log.info(f"{step.name} is being restarted")
#         return _step_run_dir_when_restarting(parent_run, step_name)
#     _maybe_rm_dir_symlink(parent_run, step_name)
#     step_run_dir = _step_run_dir_when_not_restarting(parent_run)
#     steps_util.link_to_step_run(step_name, step_run_dir, parent_run.dir)
#     return step_run_dir


def _resolve_step_run_dir(parent_run, step_name):
    """Returns a resolved step run directory path.

    A resolved dir may be an existing run directory or a to-be-created
    run directory associated with a step dir link.

    An existing directory is one linked to from an step dir link. A
    to-be-created directory is a generated path to a non-existing run
    directory that is similarly linked to. In this case the link is
    initially broken and later resolved when the run is started.
    """
    step_dir_link = _step_dir_link(parent_run, step_name)
    return util.find_apply(
        [
            _existing_step_run_dir,
            _new_step_run_dir,
        ],
        step_dir_link,
    )


def _existing_step_run_dir(step_dir_link):
    """Returns resolved link dest for dir link if exists.

    If `step_dir_link` is not a link or does not point to a directory,
    returns None.
    """
    if not os.path.islink(step_dir_link):
        return None
    link_realpath = util.realpath(step_dir_link)
    if not os.path.isdir(link_realpath):
        return None
    return link_realpath


def _new_step_run_dir(step_dir_link):
    """Returns a generated run directory target of step dir link.

    Creates a link to the generated run directory but does not create
    the run directory.

    Assumes that step dir link does not exist. If it does exist,
    failed with an error message.

    Assumes that step dir link is an immediate subdirectory of the
    parent run and that the parent run is located in the runs
    directory.

    The returned generated step run dir is located in the runs
    directory.
    """
    _handle_broken_link(step_dir_link)
    step_run_dir = _generate_run_dir_for_link(step_dir_link)
    _make_run_dir_link(step_dir_link, step_run_dir)
    return step_run_dir


def _handle_broken_link(step_dir_link):
    """Deletes step dir link if broken.

    If step dir link exists and is not a link, fails with an error
    message.
    """
    if not os.path.exists(step_dir_link):
        return
    if not os.path.islink(step_dir_link):
        _error(f"unexpected step run link {step_dir_link}: expected symlink")
    os.remove(step_dir_link)


def _generate_run_dir_for_link(step_dir_link):
    """Generates a path for a to-be-creatd run directory."""
    parent_run_dir = os.path.dirname(step_dir_link)
    runs_dir = os.path.dirname(parent_run_dir)
    return os.path.join(runs_dir, runlib.mkid())


def _make_run_dir_link(step_dir_link, step_run_dir):
    rel_step_run_dir = os.path.relpath(step_run_dir, os.path.dirname(step_dir_link))
    os.symlink(rel_step_run_dir, step_dir_link)


def _step_run_exists(parent_run, step_name):
    step_dir_link = _step_dir_link(parent_run, step_name)
    return os.path.exists(step_dir_link)


def _step_dir_link(parent_run, step_name):
    return os.path.join(parent_run.dir, step_name)


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


def _run_step(step, parent_run, step_run_dir):
    cmd = _step_run_cmd(step, step_run_dir, parent_run)
    env = _step_run_env(step, parent_run)
    cwd = _step_run_cwd()
    _log_step_details(step_run_dir, step, cmd, env, cwd)
    returncode = subprocess.call(cmd, env=env, cwd=cwd)
    if returncode != 0:
        sys.exit(returncode)


def _log_step_details(step_run_dir, step, cmd, env, cwd):
    log.info(
        "%s %s: %s",
        "restarting" if _restarting_step(step_run_dir) else "running",
        step,
        _format_step_cmd(cmd),
    )
    log.debug("step cwd %s", cwd)
    log.debug("step command: %s", cmd)
    log.debug("step env: %s", env)


def _step_run_cmd(step, step_run_dir, parent_run):
    return (
        _step_run_base_args()
        + _step_run_type_args(step, step_run_dir, parent_run)
        + _step_run_parent_passthrough_args(parent_run)
        + _step_run_step_config_args(step)
    )


def _step_run_base_args():
    return [
        config.python_exe(),
        "-um",
        "guild.main_bootstrap",
        "run",
        "-y",
    ]


def _step_run_type_args(step, step_run_dir, parent_run):
    if _restarting_step(step_run_dir):
        return _step_run_restart_args(step_run_dir, parent_run)
    return _step_run_dir_args(step, step_run_dir)


def _restarting_step(step_run_dir):
    return os.path.exists(step_run_dir)


def _step_run_restart_args(step_run_dir, parent_run):
    step_run_id = _restartable_id_for_step_run_dir(step_run_dir, parent_run)
    return ["--restart", step_run_id]


def _restartable_id_for_step_run_dir(step_run_dir, parent_run):
    """Returns a confirmed restartable run ID for a step dir.

    Asserts that the step and parent runs are both located in the same
    parent directory - i.e. they're peers.
    """
    step_run_dir_parent, step_run_id = os.path.split(step_run_dir)
    assert util.compare_paths(step_run_dir_parent, os.path.dirname(parent_run.dir)), (
        step_run_dir,
        parent_run.dir,
    )
    return step_run_id


def _step_run_dir_args(step, step_run_dir):
    return ["--run-dir", step_run_dir, step.op_spec]


def _step_run_parent_passthrough_args(parent_run):
    opts = []
    params = parent_run.get("run_params")
    if params.get("stage_trials"):
        opts.append("--stage-trials")
    return opts


def _step_run_step_config_args(step):
    args = []
    if step.batch_label:
        args.extend(["--batch-label", step.batch_label])
    for tag in step.batch_tags:
        args.extend(["--batch-tag", tag])
    if step.fail_on_trial_error:
        args.append("--fail-on-trial-error")
    if step.force_flags:
        args.append("--force-flags")
    if step.gpus is not None:
        args.extend(["--gpus", str(step.gpus)])
    if step.label:
        args.extend(["--label", step.label])
    if step.max_trials:
        args.extend(["--max-trials", str(step.max_trials)])
    if step.maximize:
        args.extend(["--maximize", step.maximize])
    if step.minimize:
        args.extend(["--minimize", step.minimize])
    if step.needed:
        args.append("--needed")
    if step.no_gpus:
        args.append("--no-gpus")
    for flag in step.opt_flags:
        args.extend(["--opt-flag", flag])
    if step.optimize:
        args.append("--optimize")
    if step.optimizer:
        args.extend(["--optimizer", step.optimizer])
    if step.random_seed is not None:
        args.extend(["--random-seed", str(step.random_seed)])
    if step.remote:
        args.extend(["--remote", step.remote])
    if step.stop_after:
        args.extend(["--stop-after", str(step.stop_after)])
    for tag in step.tags:
        args.extend(["--tag", tag])
    args.extend([f"@{file}" for file in step.batch_files])
    args.extend(flag_util.flag_assigns(step.flags))
    return args


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
    """Returns user-facing formatted cmd.

    `cmd` may take one or two forms: a restart command or a
    run-with-directory command. The formatted commands differs based
    on the cmd form.
    """
    return _try_format_run_dir_cmd(cmd) or _format_restart_cmd(cmd)


def _try_format_run_dir_cmd(cmd):
    try:
        run_dir_pos = cmd.index("--run-dir")
    except ValueError:
        return None
    else:
        assert run_dir_pos == 5, cmd
        # Args following --run-dir <dir>
        return " ".join(cmd[run_dir_pos + 2 :])


def _format_restart_cmd(cmd):
    try:
        restart_pos = cmd.index("--restart")
    except ValueError:
        assert False, cmd
    else:
        assert restart_pos == 5, cmd
        # Args following --restart
        return " ".join(cmd[restart_pos + 1 :])


def _run_step_checks(step, step_run_dir):
    """Applies check config to completed step run in run_dir.

    Raises CheckFailed if a check fails.
    """
    if not step.checks:
        return
    passed = []
    failed = []
    for check in step.checks:
        try:
            check.check_run(runlib.for_dir(step_run_dir))
        except run_check.Failed as e:
            log.error("check failed: %s", e)
            failed.append(check)
        else:
            passed.append(check)
    log.info("%i of %i checks passed", len(passed), len(step.checks))
    if failed:
        _error(
            "stopping because a check failed - see above for details",
            exit_code.TEST_FAILED,
        )


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
