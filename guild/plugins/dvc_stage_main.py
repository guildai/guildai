# Copyright 2017-2022 TensorHub, Inc.
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

import argparse
import logging
import os
import re
import shutil
import subprocess

import yaml

from guild import config
from guild import op_util
from guild import util

from guild.commands import run_impl

log = None

PIPELINE_STAGE_PS = [
    re.compile(r"Stage '(.*?)' didn't change, skipping"),
    re.compile(r"Running stage '(.*?)':"),
]


class _Pipeline:
    def __init__(self, target_stage, project_dir):
        _assert_dvc_yaml(project_dir)
        self.target_stage = target_stage
        self.project_dir = project_dir
        self.ran_stages = []
        self.dvc_yaml = _load_dvc_yaml(project_dir)


def _assert_dvc_yaml(project_dir):
    dvc_yaml = os.path.join(project_dir, "dvc.yaml")
    if not os.path.exists(dvc_yaml):
        _missing_dvc_yaml_error(project_dir)


def _load_dvc_yaml(dir):
    with open(os.path.join(dir, "dvc.yaml")) as f:
        return yaml.safe_load(f)


def main():
    op_util.init_logging()
    globals()["log"] = logging.getLogger("guild")
    args = _init_args()
    pipeline = _Pipeline(args.stage, args.project_dir)
    if args.pipeline:
        _handle_pipeline(pipeline)
    else:
        _handle_stage(pipeline)


def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument("--pipeline", action="store_true")
    p.add_argument("--project-dir")
    p.add_argument("stage")
    args = p.parse_args()
    _ensure_project_dir_arg(args)
    return args


def _ensure_project_dir_arg(args):
    if not args.project_dir:
        project_dir_env = os.getenv("PROJECT_DIR")
        if not project_dir_env:
            raise SystemExit(
                "unspecified project dir - specify either --project-dir "
                "or set the PROJECT_DIR environment variable"
            )
        args.project_dir = project_dir_env


def _missing_dvc_yaml_error(project_dir):
    raise SystemExit(
        "invalid DvC config directory '%s' - missing dvc.yaml" % project_dir
    )


def _handle_pipeline(pipeline):
    for stage in _iter_pipeline_stages(pipeline):
        _assert_not_ran_pipeline_stage(stage, pipeline)
        _run_pipeline_stage(stage, pipeline)
        pipeline.ran_stages.append(stage)
    _assert_target_stage_ran(pipeline)


def _iter_pipeline_stages(pipeline):
    out = _repro_dry_run_for_pipeline(pipeline)
    for line in out.split("\n"):
        stage = _pipeline_stage_for_line(line)
        if stage:
            yield stage


def _pipeline_stage_for_line(line):
    for p in PIPELINE_STAGE_PS:
        m = p.match(line)
        if m:
            return m.group(1)
    return None


def _repro_dry_run_for_pipeline(pipeline):
    cmd = [
        "dvc",
        "repro",
        "--dry",
        pipeline.target_stage,
    ]
    log.debug("dvc repro dry run cmd: %s", cmd)
    p = subprocess.Popen(
        cmd,
        cwd=pipeline.project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    log.debug(
        "dvc repro dry run result:\n%s---\n%s---\n%i",
        _lazy_decode(out),
        _lazy_decode(err),
        p.returncode,
    )
    if p.returncode != 0:
        _dvc_pipeline_status_error(err, p.returncode)
    assert not err, (err, out)
    return out.decode("utf-8", errors="ignore")


class _lazy_decode:
    def __init__(self, s):
        self.s = s

    def __str__(self):
        if self.s is None:
            return None
        return self.s.decode("utf-8", errors="ignore")


def _dvc_pipeline_status_error(err_raw, returncode):
    err = err_raw.decode("utf-8", errors="ignore").strip()
    raise SystemExit("error getting DvC pipeline status: %s (%i)" % (err, returncode))


def _assert_not_ran_pipeline_stage(stage, pipeline):
    if stage in pipeline.ran_stages:
        ran_desc = ", ".join(pipeline.ran_stages)
        raise SystemExit(
            "cycle detected in pipeline stages: trying to run "
            "'%s' but already ran %s" % (stage, ran_desc)
        )


def _run_pipeline_stage(stage, pipeline):
    with config.SetCwd(pipeline.project_dir):
        run_impl.run(opspec="dvc.yaml:%s" % stage)


def _assert_target_stage_ran(pipeline):
    if pipeline.target_stage not in pipeline.ran_stages:
        ran_desc = ", ".join(pipeline.ran_stages)
        raise SystemError(
            "failed to run target stage '%s' in pipeline %s"
            % (pipeline.target_stage, ran_desc)
        )


def _handle_stage(pipeline):
    stage_outputs = _target_stage_outputs(pipeline)
    log.info("Running DvC stage %s", pipeline.target_stage)
    _repro_run_for_pipeline(pipeline)
    log.info("Copying stage outputs to run directory")
    _copy_stage_outputs_to_run_dir(stage_outputs, pipeline.project_dir)


def _target_stage_outputs(pipeline):
    stage_data = pipeline.dvc_yaml.get("stages", {}).get(pipeline.target_stage, {})
    return stage_data.get("outs", [])


def _repro_run_for_pipeline(pipeline):
    cmd = [
        "dvc",
        "repro",
        pipeline.target_stage,
    ]
    log.debug("dvc repro cmd: %s", cmd)
    p = subprocess.Popen(cmd, cwd=pipeline.project_dir)
    returncode = p.wait()
    if returncode != 0:
        raise SystemExit(
            "'dvc repro %s' failed (exit code %i) - see above for details"
            % (util.shlex_quote(pipeline.target_stage), returncode)
        )


def _copy_stage_outputs_to_run_dir(outputs, source_dir):
    run_dir = _required_run_dir()
    for path in outputs:
        log.info("Copying %s", path)
        src = os.path.join(source_dir, path)
        log.debug("copying stage output '%s' to run directory '%s'", src, run_dir)
        shutil.copy(src, run_dir)


def _required_run_dir():
    run_dir = os.getenv("RUN_DIR")
    if not run_dir:
        raise SystemExit("missing required environment RUN_DIR for operation")
    return run_dir


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        op_util.handle_system_exit(e)
