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

import logging
import os
import re
import shlex
import subprocess
import sys

import click
import six

import guild.log
import guild.opref
import guild.run

from guild import exit_code
from guild import op_util
from guild import run_check
from guild import util

log = None # intialized in _init_logging

class Step(object):

    used_params = (
        "disable_plugins",
        "flags",
        "gpus",
        "label",
        "needed",
        "no_gpus",
        "opspec",
        "opt_flags",
        "stop_after",
    )

    def __init__(self, data, parent_flags, parent_opref):
        if isinstance(data, six.string_types):
            data = {
                "run": data
            }
        if not isinstance(data, dict):
            _error("invalid step data: %r" % data)
        params = self._parse_run(data)
        assert params["opspec"], params
        opspec_param = params["opspec"]
        self.op_spec = self._apply_default_model(opspec_param, parent_opref)
        self.name = data.get("name") or opspec_param
        self.flags = self._init_flags(params, parent_flags)
        self.checks = self._init_checks(data)
        self.label = self._resolve_param(params, "label", parent_flags)
        self.disable_plugins = self._resolve_param(
            params, "disable_plugins", parent_flags)
        self.gpus = self._resolve_param(params, "gpus", parent_flags)
        self.no_gpus = params["no_gpus"]
        self.stop_after = params["stop_after"]
        self.needed = params["needed"]
        self.opt_flags = params["opt_flags"]

    def _parse_run(self, data):
        from guild.commands.run import run as run_cmd
        run_spec = data.get("run", "").strip()
        if not run_spec:
            _error("invalid step %r: must define run" % data)
        args = shlex.split(run_spec)
        try:
            ctx = run_cmd.make_context("run", args)
        except click.exceptions.ClickException as e:
            _error("invalid run spec %r: %s" % (run_spec, e))
        else:
            self._warn_ignored_params(ctx, run_spec)
            return ctx.params

    def _warn_ignored_params(self, ctx, run_spec):
        "Warn if any params set that we ignore."""
        defaults = {p.name: p.default for p in ctx.command.params}
        for name, val in sorted(ctx.params.items()):
            if name not in self.used_params and val != defaults[name]:
                log.warning(
                    "run parameter %s used in %r ignored",
                    name, run_spec)

    @staticmethod
    def _apply_default_model(step_opspec, parent_opref):
        step_opref = guild.opref.OpRef.from_string(step_opspec)
        if not step_opref.model_name:
            step_opref = guild.opref.OpRef(
                step_opref.pkg_type,
                step_opref.pkg_name,
                step_opref.pkg_version,
                parent_opref.model_name,
                step_opref.op_name)
        return step_opref.to_opspec()

    def _init_flags(self, params, parent_flags):
        try:
            parsed = op_util.parse_flags(params["flags"])
        except op_util.ArgValueError as e:
            _error("invalid argument '%s' - expected NAME=VAL" % e.arg)
        else:
            resolved = self._resolve_flag_vals(parsed, parent_flags)
            return self._remove_undefined_flags(resolved)

    @staticmethod
    def _resolve_flag_vals(flags, parent_flags):
        return {
            name: util.resolve_refs(val, parent_flags)
            for name, val in flags.items()
        }

    @staticmethod
    def _remove_undefined_flags(flag_vals):
        return {
            name: val for name, val in flag_vals.items()
            if val is not None
        }

    @staticmethod
    def _resolve_param(params, name, flags):
        resolved = util.resolve_refs(params[name], flags)
        if resolved is None:
            return resolved
        return str(resolved)

    @staticmethod
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

    def __str__(self):
        return self.name or self.op_spec

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

def _init_run():
    run_id, run_dir = _run_environ()
    return guild.run.Run(run_id, run_dir)

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
    return [Step(step_data, flags, opref) for step_data in data]

def _run_step(step, parent_run):
    step_run = _init_step_run(parent_run)
    cmd = _init_step_cmd(step, step_run.path)
    _link_to_step_run(step, step_run.path, parent_run.path)
    env = dict(os.environ)
    env["NO_WARN_RUNDIR"] = "1"
    log.info("running %s: %s", step, _format_step_cmd(cmd))
    log.debug("cmd for %s: %s", step, cmd)
    returncode = subprocess.call(cmd, env=env, cwd=os.getenv("CMD_DIR"))
    if returncode != 0:
        sys.exit(returncode)
    return step_run

def _init_step_run(parent_run):
    """Returns the run dir for a step run.

    Directory is based on a new, unique run ID but is not created.
    """
    runs_dir = os.path.dirname(parent_run.path)
    step_run_id = guild.run.mkid()
    step_run_dir = os.path.join(runs_dir, step_run_id)
    return guild.run.Run(step_run_id, step_run_dir)

def _init_step_cmd(step, step_run_dir):
    base_args = [
        sys.executable, "-um", "guild.main_bootstrap",
        "run", "-y",
        "--run-dir", step_run_dir,
        step.op_spec]
    step_options = _step_options(step)
    flag_args = _step_flag_args(step)
    return base_args + step_options + flag_args

def _step_options(step):
    opts = []
    if step.label:
        opts.extend(["--label", step.label])
    if step.disable_plugins:
        opts.extend(["--disable-plugins", step.disable_plugins])
    if step.gpus is not None:
        opts.extend(["--gpus", step.gpus])
    elif step.no_gpus:
        opts.append("--no-gpus")
    if step.stop_after:
        opts.extend(["--stop-after", step.stop_after])
    if step.needed:
        opts.append("--needed")
    for flag in step.opt_flags:
        opts.extend(["--opt-flag", flag])
    return opts

def _step_flag_args(step):
    if not step.flags:
        return []
    return [
        "%s=%s" % (name, val)
        for name, val in sorted(step.flags.items())
    ]

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
        if not os.path.exists(path):
            return path
        path = "%s_%i" % (path_base, v)
        v += 1

def _format_step_cmd(cmd):
    from six.moves import shlex_quote
    # Just show opspec on - assert front matter to catch changes to cmd.
    assert cmd[0:6] == [
        sys.executable, "-um", "guild.main_bootstrap",
        "run", "-y", "--run-dir"
    ], cmd
    return " ".join([shlex_quote(arg) for arg in cmd[7:]])

def _maybe_check_step_run(step, run):
    if not step.checks:
        return
    if _run_skipped(run):
        log.info("skipping checks for %s", step.name)
        return
    checks_passed = _check_step_run(step, run)
    if not checks_passed:
        _error(
            "stopping because a check failed",
            exit_code.TEST_FAILED)

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

def _internal_error(msg):
    sys.stderr.write("guild.steps_main: %s\n" % msg)
    sys.exit(exit_code.INTERNAL_ERROR)

def _error(msg, exit_code=exit_code.DEFAULT):
    sys.stderr.write("guild: %s\n" % msg)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
