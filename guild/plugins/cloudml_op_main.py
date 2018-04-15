# Copyright 2017-2018 TensorHub, Inc.
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
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import dateutil.parser
import dateutil.tz
import yaml

import guild.op
import guild.run

from guild import click_util
from guild import op_util
from guild import opref
from guild import util
from guild import var

from guild.commands import runs_impl

log = logging.getLogger("guild.cloudml")

BACKGROUND_SYNC_INTERVAL = 60
BACKGROUND_SYNC_STOP_TIMEOUT = 10
WATCH_POLLING_INTERVAL = 5

DEFAULT_REGION = "us-central1"
DEFAULT_RUNTIME_VERSION = "1.4"

PRE_RUNNING_STATES = ["QUEUED", "PREPARING"]
FINAL_STATES = ["SUCCEEDED", "FAILED", "CANCELLED"]

class CloudSDK(object):

    def __init__(self, gsutil, gcloud):
        self.gsutil = gsutil
        self.gcloud = gcloud

class Sync(object):

    def __init__(self, run, watch, sdk):
        self.run = run
        self.watch = watch
        self.sdk = sdk
        self._last_sync = None

    def __call__(self):
        if self.watch:
            self._watch()
        else:
            self._run_once()

    def _watch(self):
        job_name = self.run.get("cloudml_job_name")
        if not job_name:
            log.error(
                "cloudml_job_name not defined for run %s, cannot watch job",
                self.run.id)
            return
        background_sync = util.LoopingThread(
            self._run_once,
            interval=BACKGROUND_SYNC_INTERVAL,
            stop_timeout=BACKGROUND_SYNC_STOP_TIMEOUT)
        background_sync.start()
        args = [
            self.sdk.gcloud, "ml-engine", "jobs", "stream-logs",
            "--polling-interval", str(WATCH_POLLING_INTERVAL),
            job_name
        ]
        try:
            subprocess.check_call(args)
        except KeyboardInterrupt:
            pass
        finally:
            last_sync0 = self._last_sync
            background_sync.stop()
            if self._last_sync == last_sync0:
                self._run_once()
            sys.stdout.write("\n")
            sys.stdout.flush()

    def _run_once(self):
        job = self._sync_status()
        if job and job["state"] not in [PRE_RUNNING_STATES]:
            files_synced = self._sync_files(job)
            if files_synced:
                self._maybe_finalize(job)
        self._last_sync = time.time()

    def _sync_status(self):
        job_name = self.run.get("cloudml_job_name")
        if not job_name:
            log.error(
                "cloudml_job_name not defined for run %s, cannot sync status",
                self.run.id)
            return None
        log.info("Synchronizing job status for run %s", self.run.id)
        job = self._describe_job(job_name)
        if not job:
            log.error(
                "no job info for %s, cannot sync status", job_name)
            return None
        self.run.write_attr("cloudml_job_description", job)
        state = job["state"]
        log.info("Run %s is %s", self.run.id, state)
        self.run.write_attr("cloudml_job_state", state)
        return job

    def _describe_job(self, job_name):
        try:
            out = subprocess.check_output(
                [self.sdk.gcloud, "--format", "json", "ml-engine", "jobs",
                 "describe", job_name])
        except subprocess.CalledProcessError as e:
            log.error("error reading job info for %s: %s", job_name, e)
            return None
        else:
            return json.loads(out)

    @staticmethod
    def _exit_status_for_job_state(state):
        if state == "SUCCEEDED":
            return 0
        elif state == "FAILED":
            return 1
        elif state == "CANCELLED":
            return 2
        else:
            raise AssertionError(state)

    def _sync_files(self, job):
        job_dir = self.run.get("cloudml_job_dir")
        if not job_dir:
            log.error(
                "cloudml_job_dir undefined for run %s - cannot sync files",
                self.run.id)
            return False
        if self.run.get("_cloudml_hptuning"):
            trials = job.get("trainingOutput", {}).get("trials", [])
            return self._hptune_sync_files(job_dir, trials)
        else:
            return self._default_sync_files(job_dir)

    def _hptune_sync_files(self, job_dir, trials):
        trial_runs = self.run.get("_cloudml_trials", {})
        all_synced = True
        for trial in trials:
            run = None
            trial_id = trial["trialId"]
            trial_run_id = trial_runs.get(trial_id)
            if trial_run_id:
                try:
                    run = var.get_run(trial_run_id)
                except LookupError:
                    log.warning("trial run %s does not exist, will recreate")
            if run is None:
                run = guild.op.init_run()
                log.info(
                    "Initializing run %s for trial %s",
                    run.id, trial_id)
                trial_runs[trial_id] = run.id
                self.run.write_attr("_cloudml_trials", trial_runs)
                self._init_trial_run(run, trial)
            synced = self._maybe_sync_trial_run(job_dir, trial_id, run)
            all_synced = all_synced and synced
        return all_synced

    def _init_trial_run(self, run, trial):
        run.init_skel()
        run.write_attr("opref", self.run.get("opref"))
        run.write_attr("started", self._trial_started(trial))
        run.write_attr("exit_status", 0)
        run.write_attr("exit_status.remote", 0)
        flags = self.run.get("flags")
        flag_map = self.run.get("_flag_map")
        for name, val in trial.get("hyperparameters", {}).items():
            flags[flag_map.get(name, name)] = val
        run.write_attr("flags", flags)
        run.write_attr("label", self._trial_label(trial))
        for attr in self.run.attr_names():
            if attr.startswith("_extra_"):
                run.write_attr(attr, self.run.get(attr))
        job_name = self.run.get("cloudml_job_name")
        run.write_attr("cloudml_job_name", job_name)
        trial_id = trial["trialId"]
        run.write_attr("cloudml_trial_id", trial_id)
        job_dir = "%s/%s" % (self.run.get("cloudml_job_dir"), trial_id)
        run.write_attr("cloudml_job_dir", job_dir)

    def _trial_started(self, trial):
        # Hack to order trials in descending order: add int(trial id)
        # to host_started
        started = self.run.get("started")
        try:
            trial_pos = int(trial["trialId"])
        except ValueError:
            return started
        else:
            return started + trial_pos

    def _trial_label(self, trial):
        return "%s-trial-%s" % (self.run.short_id, trial["trialId"])

    def _maybe_sync_trial_run(self, job_dir, trial_id, run):
        synced = run.get("_cloudml_trial_synced")
        if not synced:
            log.info(
                "Synchronizing trial %s for run %s to %s",
                trial_id, self.run.id, run.id)
            synced = self._rsync("%s/%s" % (job_dir, trial_id), run.path)
            if synced:
                run.write_attr("_cloudml_trial_synced", guild.run.timestamp())
        return synced

    def _default_sync_files(self, job_dir):
        log.info("Synchronizing job for run %s", self.run.id)
        return self._rsync(job_dir, self.run.path, ignore=self._run_links())

    def _run_links(self):
        links = []
        run_path_len = len(self.run.path)
        for path, dirs, files in os.walk(self.run.path):
            for name in dirs + files:
                fullpath = os.path.join(path, name)
                if os.path.islink(fullpath):
                    links.append(fullpath[run_path_len + 1:])
        return links

    def _rsync(self, src, dest, ignore=None):
        args = [self.sdk.gsutil, "-m", "rsync", "-Cr"]
        exclude = self._rsync_exclude(ignore)
        if exclude:
            args.extend(["-x", exclude])
        args.extend([src, dest])
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError:
            log.error(
                "error syncing run %s files from %s (see above for details)",
                self.run.id, src)
            return False
        else:
            return True

    @staticmethod
    def _rsync_exclude(paths):
        return "|".join([re.escape(path) for path in (paths or [])])

    def _maybe_finalize(self, job):
        if job["state"] in FINAL_STATES:
            self._finalize_run(job)

    def _finalize_run(self, job):
        log.info("Finalizing run %s", self.run.id)
        exit_status = self._exit_status_for_job_state(job["state"])
        self.run.write_attr("exit_status.remote", exit_status)
        stopped = _parse_datetime_as_timestamp(job["endTime"])
        self.run.write_attr("stopped", stopped)
        self._delete_file(self.run.guild_path("LOCK.remote"))

    def _delete_file(self, filename):
        try:
            os.remove(filename)
        except OSError as e:
            if os.path.exists(filename):
                log.error(
                    "could not delete '%s' from run %s (%s)",
                    filename, self.run.id, e)

class CancelJob(object):

    def __init__(self, run, no_wait, sdk):
        self.run = run
        self.no_wait = no_wait
        self.sdk = sdk

    def __call__(self):
        job_name = self.run.get("cloudml_job_name")
        if not job_name:
            log.error(
                "cloudml_job_name not defined for run %s, cannot stop job",
                self.run.id)
            return
        self._cancel_job(job_name)
        if not self.no_wait:
            sync_run(self.run, watch=True)

    def _cancel_job(self, job_name):
        log.info("Canceling %s", job_name)
        args = [self.sdk.gcloud, "ml-engine", "jobs", "cancel", job_name]
        subprocess.call(args)

class Train(object):

    op_name = "train"

    def __init__(self, args, sdk):
        job_args, flag_args = self._parse_args(args)
        self.run = op_util.current_run()
        self.job_name = job_args.job_name or self._job_name()
        self.job_dir = "gs://%s/%s" % (job_args.bucket, self.job_name)
        self.args = job_args
        self.flag_args = flag_args
        self.package_name = self._package_name()
        self.package_version = self._package_version()
        self.sdk = sdk

    def _parse_args(self, args):
        p = self._init_arg_parser()
        return p.parse_known_args(args)

    def _init_arg_parser(self):
        p = argparse.ArgumentParser(prog="cloudml_op_main.py %s" % self.op_name)
        p.add_argument("--bucket", required=True)
        p.add_argument("--region", default=DEFAULT_REGION)
        p.add_argument("--job-name")
        p.add_argument("--runtime-version", default=DEFAULT_RUNTIME_VERSION)
        p.add_argument("--module-name", required=True)
        p.add_argument("--scale-tier")
        p.add_argument("--config")
        return p

    def _job_name(self):
        return "guild_train_%s" % self.run.id

    def _package_name(self):
        from guild.opref import OpRef
        opref = OpRef.from_run(self.run)
        return opref.model_name

    def _package_version(self):
        return "0.0.0+%s" % self.run.short_id

    def __call__(self):
        self._init_package()
        self._init_job_dir()
        self._submit_job()
        self._write_lock()
        if self.run.get("_no-wait"):
            log.info(
                "no-wait specified, exiting early\n"
                "Job %s will continue to run remotely - use 'guild sync' "
                "to synchronize job status.", self.job_name)
            return
        self._sync()

    def _init_package(self):
        env = {
            "PYTHONPATH": os.path.pathsep.join(sys.path),
            "PACKAGE_NAME": self.package_name,
            "PACKAGE_VERSION": self.package_version,
        }
        # Use an external process because setuptools assumes it's a
        # command line app.
        try:
            subprocess.check_call(
                [sys.executable, "-um", "guild.plugins.training_pkg_main"],
                env=env,
                cwd=self.run.path)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    def _init_job_dir(self):
        self.run.write_attr("cloudml_job_dir", self.job_dir)
        for name in os.listdir(self.run.path):
            if name.startswith(".guild"):
                continue
            src = os.path.join(self.run.path, name)
            dest = self.job_dir + "/" + name
            self._recursive_copy_files(src, dest)

    def _recursive_copy_files(self, src, dest):
        try:
            subprocess.check_call(
                [self.sdk.gsutil, "-m", "cp", "-r", src, dest])
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    def _submit_job(self):
        args = [
            self.sdk.gcloud, "ml-engine", "jobs",
            "submit", "training", self.job_name,
            "--job-dir", self.job_dir,
            "--packages", self._find_package_name(),
            "--module-name", self.args.module_name,
            "--region", self.args.region,
            "--runtime-version", self.args.runtime_version,
        ]
        if self.args.scale_tier:
            args.extend(["--scale-tier", self.args.scale_tier])
        if self.args.config:
            args.extend(["--config", self.args.config])
        if self.flag_args:
            args.append("--")
            resolved_flag_args = self._apply_job_dir(self.flag_args)
            args.extend(resolved_flag_args)
        log.info("Starting job %s in %s", self.job_name, self.job_dir)
        log.debug("gutil cmd: %r", args)
        self.run.write_attr("cloudml_job_name", self.job_name)
        self.run.write_attr("cloudml_job_cmd", args)
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    def _apply_job_dir(self, args):
        """Applies job dir to args that reference local files."""
        def f(val):
            if os.path.exists(val):
                if val == ".":
                    val = self.job_dir
                else:
                    val = os.path.join(self.job_dir, val)
            return val
        return [f(arg) for arg in args]

    def _find_package_name(self):
        package_name = _safe_name(self.package_name)
        path = "%s-%s-py2.py3-none-any.whl" % (package_name, self.package_version)
        assert os.path.exists(path), path
        return path

    def _write_lock(self):
        with open(self.run.guild_path("LOCK.remote"), "w") as f:
            f.write("cloudml")

    def _sync(self):
        sync = Sync(self.run, True, self.sdk)
        sync()

class HPTune(Train):

    op_name = "hptune"

    def __init__(self, args, sdk):
        super(HPTune, self).__init__(args, sdk)
        self._patch_hptuning_config()

    def _init_arg_parser(self):
        p = super(HPTune, self)._init_arg_parser()
        p.add_argument("--max-trials", type=int)
        p.add_argument("--max-parallel-trials", type=int)
        p.add_argument("--resume-from")
        return p

    def _job_name(self):
        return "guild_hptune_%s" % self.run.id

    def _patch_hptuning_config(self):
        tuning_config = {}
        if self.args.max_trials:
            tuning_config["maxTrials"] = self.args.max_trials
        if self.args.max_parallel_trials:
            tuning_config["maxParallelTrials"] = self.args.max_parallel_trials
        if self.args.resume_from:
            job_name = self._run_job_name(self.args.resume_from)
            tuning_config["resumePreviousJobId"] = job_name
        if tuning_config:
            config = self._apply_tuning_config(tuning_config)
            self._ensure_compatible_config(config)
            self._replace_config(config)

    @staticmethod
    def _run_job_name(run_prefix):
        run = _one_run(run_prefix)
        name = run.get("cloudml_job_name")
        if not name:
            _exit("unable to find cloudml job for run %s", run.id)
        return name

    def _apply_tuning_config(self, tuning_config):
        config = self._load_config()
        training_input = config.setdefault("trainingInput", {})
        hparams = training_input.setdefault("hyperparameters", {})
        hparams.update(tuning_config)
        return config

    def _load_config(self):
        assert self.args.config, "--config required for hptune"
        with open(self.args.config, "r") as f:
            return yaml.safe_load(f)

    @staticmethod
    def _ensure_compatible_config(config):
        hparams = config["trainingInput"]["hyperparameters"]
        if "resumePreviousJobId" in hparams:
            hparams.pop("goal", None)
            hparams.pop("params", None)
            hparams.pop("hyperparameterMetricTag", None)

    def _replace_config(self, config):
        fh, path = tempfile.mkstemp(
            prefix="hptuning_config_generated-",
            suffix=".yaml",
            dir=self.run.path)
        with os.fdopen(fh, "w") as f:
            yaml.safe_dump(config, f)
        self.args.config = path

    def _init_job_dir(self):
        super(HPTune, self)._init_job_dir()
        self.run.write_attr("_cloudml_hptuning", True)

class Deploy(object):

    op_name = "deploy"

    def __init__(self, args, sdk):
        self.args = self._parse_args(args)
        self.run = op_util.current_run()
        self.trained_run = _find_run(
            self.args.trained_model,
            self.run,
            ["cloudml-train", "cloudml-hptune", "train"])
        self.opref = opref.OpRef.from_run(self.trained_run)
        self.model_name = self.args.model or self.opref.model_name
        self.safe_model_name = _safe_name(self.model_name)
        self.region = self.args.region or self._run_region() or DEFAULT_REGION
        self.model_version = self.args.version or self._model_version()
        self.sdk = sdk

    def _parse_args(self, args):
        p = self._init_arg_parser()
        return p.parse_known_args(args)[0]

    def _init_arg_parser(self):
        p = argparse.ArgumentParser(prog="cloudml_op_main.py %s" % self.op_name)
        p.add_argument("--trained_model")
        p.add_argument("--version")
        p.add_argument("--region")
        p.add_argument("--bucket")
        p.add_argument("--model-binaries")
        p.add_argument("--model")
        p.add_argument("--runtime-version", default=DEFAULT_RUNTIME_VERSION)
        p.add_argument("--config")
        return p

    def _run_region(self):
        return self.trained_run.get("flags", {}).get("region")

    def _model_version(self):
        return "v_%s" % self.run.id

    def __call__(self):
        self._validate_args()
        self._init_run()
        self._ensure_model()
        self._create_version()

    def _validate_args(self):
        job_dir = self.trained_run.get("cloudml_job_dir")
        if (not job_dir and
            not self.args.bucket and
            not self.args.model_binaries):
            _exit(
                "missing required flags 'bucket' or 'model-binaries' "
                "(specifies where model binaries should be uploaded for "
                "deployment)")

    def _init_run(self):
        if not self.run.get("label"):
            self.run.write_attr("label", "%s-deploy" % self.trained_run.short_id)

    def _ensure_model(self):
        self.run.write_attr("cloudml_model_name", self.safe_model_name)
        args = [
            self.sdk.gcloud, "ml-engine", "models", "create",
            self.safe_model_name, "--regions", self.region
        ]
        log.info("Creating model %s", self.safe_model_name)
        p = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _out, err = p.communicate()
        if "model with the same name already exists" in err.decode("utf-8"):
            log.info("Model %s already exists", self.safe_model_name)
        elif p.returncode != 0:
            _exit(err, code=p.returncode)

    def _create_version(self):
        model_binaries = self._ensure_model_binaries()
        self.run.write_attr("cloudml_model_binaries", model_binaries)
        self.run.write_attr("cloudml_model_version", self.model_version)
        self.run.write_attr("trained_model_run", self.trained_run.id)
        log.info("Using trained model from run %s", self.trained_run.id)
        log.info("Creating version %s", self.model_version)
        args = [
            self.sdk.gcloud, "ml-engine", "versions", "create",
            self.model_version,
            "--model", self.safe_model_name,
            "--origin", model_binaries,
            "--runtime-version", self.args.runtime_version,
        ]
        if self.args.config:
            args.extend(["--config", self.args.config])
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    def _ensure_model_binaries(self):
        if not self.trained_run.has_attr("cloudml_job_dir"):
            upload_path = self._upload_model_binaries()
            return upload_path
        else:
            return self._job_dir_model_binaries_path()

    def _upload_model_binaries(self):
        src = self._run_model_binaries_path()
        dest = self._remote_model_binaries(src)
        try:
            subprocess.check_call(
                [self.sdk.gsutil, "-m", "rsync", "-r", src, dest])
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)
        else:
            return dest

    def _run_model_binaries_path(self):
        saved_models = list(self._iter_saved_models(self.trained_run.path))
        if not saved_models:
            _exit("could not find a saved model in %s" % self.trained_run.path)
        return self._latest_saved_model(saved_models)

    @staticmethod
    def _iter_saved_models(dir):
        for root, dirs, files in os.walk(dir):
            try:
                dirs.remove(".guild")
            except ValueError:
                pass
            if "saved_model.pb" in files or "saved_model.pbtxt" in files:
                yield root

    @staticmethod
    def _latest_saved_model(saved_models):
        return sorted(saved_models)[-1]

    def _remote_model_binaries(self, local_model_path):
        assert self.args.bucket or self.args.model_binaries
        return self.args.model_binaries or (
            "gs://%s/guild_model_%s_%s" % (
                self.args.bucket,
                self.safe_model_name,
                os.path.basename(local_model_path)))

    def _job_dir_model_binaries_path(self):
        export_path = self._trained_run_remote_export_path()
        log.info("Looking for model binaries in %s", export_path)
        try:
            out = subprocess.check_output([
                self.sdk.gsutil, "ls", export_path + "/*/"])
        except subprocess.CalledProcessError as e:
            log.error(
                "error finding model binaries in "
                "%s (see above for details)", export_path)
            sys.exit(e.returncode)
        else:
            paths = out.split()
            return self._one_timestamp_path(paths, export_path)

    def _one_timestamp_path(self, paths, root):
        ts_paths = [path for path in paths if self._is_timestamp_path(path)]
        if not ts_paths:
            _exit("cannot find model timestamp directory in %s", root)
        ts_path = sorted(ts_paths, reverse=True)[0]
        if len(ts_paths) > 1:
            log.warning(
                "found multiple timestamp paths under %s, using %s",
                root, ts_path)
        return ts_path

    @staticmethod
    def _is_timestamp_path(path):
        parts = re.split(r"[/\\]", path)
        while parts and parts[-1] == "":
            parts.pop()
        try:
            int(parts[-1])
        except ValueError:
            return False
        else:
            return True

    def _trained_run_remote_export_path(self):
        job_dir = self.trained_run.get("cloudml_job_dir")
        assert job_dir
        return "%s/export" % job_dir

class Predict(object):

    op_name = "predict"

    def __init__(self, args, sdk):
        self.args = self._parse_args(args)
        self.run = op_util.current_run()
        self.args.instances = op_util.resolve_file(self.args.instances)
        self.deployed_run = _find_run(
            self.args.deployed_model,
            self.run,
            ["cloudml-deploy"])
        self.model_name = self._model_name()
        self.model_version = self._model_version()
        self.sdk = sdk

    def _parse_args(self, args):
        p = self._init_arg_parser()
        return p.parse_known_args(args)[0]

    def _init_arg_parser(self):
        p = argparse.ArgumentParser(prog="cloudml_op_main.py %s" % self.op_name)
        p.add_argument("--deployed-model")
        p.add_argument("--instances", required=True)
        p.add_argument("--instance-type")
        p.add_argument("--output-format")
        return p

    def _model_name(self):
        val = self.deployed_run.get("cloudml_model_name")
        if not val:
            _exit(
                "cannot predict with run %s: missing cloudml_model_name "
                "attribute", self.deployed_run.short_id)
        return val

    def _model_version(self):
        val = self.deployed_run.get("cloudml_model_version")
        if not val:
            _exit(
                "cannot predict with run %s: missing cloudml_model_version "
                "attribute", self.deployed_run.short_id)
        return val

    def __call__(self):
        self._validate_args()
        self._init_run()
        self._predict()

    def _validate_args(self):
        if not os.path.exists(self.args.instances):
            _exit("%s does not exist" % self.args.instances)

    def _init_run(self):
        shutil.copyfile(self.args.instances, "prediction.inputs")
        self.run.write_attr("cloudml_model_name", self.model_name)
        self.run.write_attr("cloudml_model_version", self.model_version)
        if not self.run.get("label"):
            self.run.write_attr(
                "label", "%s-predict" % self.deployed_run.short_id)

    def _predict(self):
        args = [self.sdk.gcloud]
        if self.args.output_format:
            args.extend(["--format", self.args.output_format])
        args.extend([
            "ml-engine", "predict",
            "--model", self.model_name,
            "--version", self.model_version,
        ])
        args.extend(self._instances_args())
        try:
            out = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)
        else:
            sys.stdout.write(out.decode())
            self._write_prediction_results(out)

    def _instances_args(self):
        # Use self.args.instances to infer file type as per its
        # extension
        format = (
            self.args.instance_type
            or self._instance_type_from_path(self.args.instances))
        # Use "prediction.inputs" as the instances location, which was
        # copied in _init_run
        instances = "prediction.inputs"
        if format == "json":
            return ["--json-instances", instances]
        else:
            if format != "text":
                log.warning(
                    "unknown instance type '%s' - assuming 'text'", format)
            return ["--text-instances", instances]

    @staticmethod
    def _instance_type_from_path(path):
        _, ext = os.path.splitext(path)
        if ext.lower() == ".json":
            return "json"
        else:
            return "text"

    @staticmethod
    def _write_prediction_results(results):
        with open("prediction.results", "w") as f:
            f.write(results.decode())

class BatchPredict(Predict):

    op_name = "batch-predict"

    def __init__(self, args, sdk):
        super(BatchPredict, self).__init__(args, sdk)
        self.job_name = self.args.job_name or self._job_name()
        self.job_dir = "gs://%s/%s" % (self.args.bucket, self.job_name)

    def _init_arg_parser(self):
        p = super(BatchPredict, self)._init_arg_parser()
        p.add_argument("--bucket", required=True)
        p.add_argument("--region", default=DEFAULT_REGION)
        p.add_argument("--job-name")
        return p

    def _job_name(self):
        return "guild_predict_%s" % self.run.id

    def __call__(self):
        self._validate_args()
        input_paths = self._init_job_dir()
        self._submit_job(input_paths)
        self._write_lock()
        self._sync()

    def _init_job_dir(self):
        self.run.write_attr("cloudml_job_dir", self.job_dir)
        src = self.args.instances
        dest = "%s/%s" % (self.job_dir, "prediction.inputs")
        try:
            subprocess.check_call([self.sdk.gsutil, "-m", "cp", src, dest])
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)
        return dest

    def _submit_job(self, input_paths):
        args = [
            self.sdk.gcloud, "ml-engine", "jobs",
            "submit", "prediction", self.job_name,
            "--model", self._model_name(),
            "--version", self._model_version(),
            "--data-format", "TEXT",
            "--region", self.args.region,
            "--input-paths", input_paths,
            "--output-path", self.job_dir,
        ]
        self.run.write_attr("cloudml_job_name", self.job_name)
        log.info("Starting job %s in %s", self.job_name, self.job_dir)
        log.debug("gutil cmd: %r", args)
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    def _write_lock(self):
        with open(self.run.guild_path("LOCK.remote"), "w") as f:
            f.write("cloudml")

    def _sync(self):
        sync = Sync(self.run, True, self.sdk)
        sync()

def _safe_name(s):
    return re.sub(r"[^0-9a-zA-Z]+", "_", s)

def _one_run(run_prefix):
    matches = list(var.find_runs(run_prefix))
    if len(matches) == 1:
        run_id, path = matches[0]
        return guild.run.Run(run_id, path)
    elif not matches:
        _exit("no runs match '%s'", run_prefix)
    else:
        run_ids = [run_id[:8] for run_id, _ in matches]
        _exit("multiple runs match '%s' (%s)", run_prefix, ", ".join(run_ids))

def _find_run(run_prefix, referring_run, for_ops):
    if run_prefix:
        return _one_run(run_prefix)
    # Simulate runs list with filter
    if not runs_impl.init_opref_attr(referring_run):
        _exit("Unable to get operation details for %s" % referring_run.id)
    model_name = referring_run.opref.model_name
    args = click_util.Args(
        ops=["%s:%s" % (model_name, op) for op in for_ops],
        completed=True,
        running=True,
        terminated=True,
        labels=[],
        runs=[],
    )
    runs = runs_impl.runs_for_args(args)
    if not runs:
        op_desc = ", ".join(args.ops)
        _exit("Cannot find a run for one of these operations: %s" % op_desc)
    return runs[0]

def _parse_datetime_as_timestamp(dt):
    parsed = dateutil.parser.parse(dt)
    local_datetime = parsed.astimezone(dateutil.tz.tzlocal())
    return int(local_datetime.strftime("%s000000"))

def _init_sdk():
    gsutil = util.which("gsutil")
    if not gsutil:
        _exit(
            "cannot find required Google Cloud Storage utility 'gsutil'\n"
            "Refer to https://cloud.google.com/storage/docs/gsutil_install"
            " for more information.")
    gcloud = util.which("gcloud")
    if not gcloud:
        _exit(
            "cannot find required Google Cloud SDK utility 'gcloud'\n"
            "Refer to https://cloud.google.com/sdk/docs/quickstarts "
            "for more information.")
    return CloudSDK(gsutil, gcloud)

def sync_run(run, watch=False):
    sync = Sync(run, watch, _init_sdk())
    sync()

def stop_run(run, no_wait):
    cancel = CancelJob(run, no_wait, _init_sdk())
    cancel()

def _exit(msg, *args, **kw):
    log.error(msg, *args)
    sys.exit(kw.get("code", 1))

def _init_op(name, op_args, sdk):
    if name == "train":
        return Train(op_args, sdk)
    elif name == "hptune":
        return HPTune(op_args, sdk)
    elif name == "deploy":
        return Deploy(op_args, sdk)
    elif name == "predict":
        return Predict(op_args, sdk)
    elif name == "batch-predict":
        return BatchPredict(op_args, sdk)
    else:
        op_util.exit("unrecognized command '%s'" % name)

def main(args):
    op_name, op_args = op_util.parse_op_args(args)
    sdk = _init_sdk()
    _init_op(op_name, op_args, sdk)()

if __name__ == "__main__":
    main(sys.argv)
