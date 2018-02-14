import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time

import guild.run

from guild import cli
from guild import cmd_impl_support
from guild import opref
from guild import plugin_util
from guild import util
from guild import var

log = logging.getLogger("cloudml")

BACKGROUND_SYNC_INTERVAL = 60
BACKGROUND_SYNC_STOP_TIMEOUT = 10
WATCH_POLLING_INTERVAL = 5

DEFAULT_REGION = "us-central1"
DEFAULT_RUNTIME_VERSION = "1.4"

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
        self._sync_run = False

    def __call__(self):
        if self.watch:
            self._watch()
        else:
            self._run_once()

    def _watch(self):
        job_name = self.run.get("cloudml-job-name")
        if not job_name:
            log.error(
                "cloudml-job-name not defined for run %s, cannot watch job",
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
            self._sync_run = False
            background_sync.stop()
            self._maybe_sync_after_watch()
            sys.stdout.write("\n")
            sys.stdout.flush()

    def _maybe_sync_after_watch(self):
        if not self._sync_run:
            self._run_once()

    def _run_once(self):
        self._sync_files()
        self._sync_status()
        self._sync_run = True

    def _sync_files(self):
        job_dir = self.run.get("cloudml-job-dir")
        if not job_dir:
            log.error(
                "cloudml-job-dir not defined for run %s, cannot sync files",
                self.run.id)
            return
        cli.out("Synchronizing job output for run %s" % self.run.id)
        self._rsync_files(job_dir, self.run.path)

    def _rsync_files(self, src, dest):
        try:
            subprocess.check_call(
                [self.sdk.gsutil, "-m", "rsync", "-Cr", src, dest])
        except subprocess.CalledProcessError:
            log.error(
                "error syncing run %s files from %s (see above for details)",
                self.run.id, src)

    def _sync_status(self):
        job_name = self.run.get("cloudml-job-name")
        if not job_name:
            log.error(
                "cloudml-job-name not defined for run %s, cannot sync status",
                self.run.id)
            return
        cli.out("Synchronizing job status for run %s" % self.run.id)
        info = self._job_info(job_name)
        if not info:
            log.error(
                "no job info for %s, cannot sync status", job_name)
            return
        self.run.write_attr("cloudml-job-description", info)
        state = info.get("state")
        cli.out("Run %s is %s" % (self.run.id, state))
        self.run.write_attr("cloudml-job-state", state)
        if state in FINAL_STATES:
            self._finalize_run(state)

    def _job_info(self, job_name):
        try:
            out = subprocess.check_output(
                [self.sdk.gcloud, "--format", "json", "ml-engine", "jobs",
                 "describe", job_name])
        except subprocess.CalledProcessError as e:
            log.error("error reading job info for %s: %s", job_name, e)
            return None
        else:
            return json.loads(out)

    def _finalize_run(self, state):
        cli.out("Finalizing run %s" % self.run.id)
        exit_status = self._exit_status_for_job_state(state)
        self.run.write_attr("exit_status.remote", exit_status)
        self._delete(self.run.guild_path("LOCK.remote"))

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

    def _delete(self, filename):
        try:
            os.remove(filename)
        except OSError as e:
            if os.path.exists(filename):
                log.error(
                    "could not delete '%s' from run %s (%s)",
                    filename, self.run.id, e)

class Train(object):

    def __init__(self, args, sdk):
        job_args, flag_args = self._parse_args(args)
        self.run = plugin_util.current_run()
        self.job_name = job_args.job_name or self._job_name()
        self.job_dir = "gs://%s/%s" % (job_args.bucket_name, self.job_name)
        self.args = job_args
        self.flag_args = flag_args
        self.package_name = self._package_name()
        self.package_version = self._package_version()
        self.sdk = sdk

    @staticmethod
    def _parse_args(args):
        p = argparse.ArgumentParser()
        p.add_argument("--bucket-name", required=True)
        p.add_argument("--region", default=DEFAULT_REGION)
        p.add_argument("--job-name")
        p.add_argument("--runtime-version", default=DEFAULT_RUNTIME_VERSION)
        p.add_argument("--module-name", required=True)
        p.add_argument("--package-path")
        p.add_argument("--scale-tier")
        p.add_argument("--config")
        return p.parse_known_args(args)

    def _job_name(self):
        return "guild_run_%s" % self.run.id

    def _package_name(self):
        from guild.opref import OpRef
        opref = OpRef.from_run(self.run)
        return opref.model_name

    def _package_version(self):
        return "0.0.0+%s" % self.run.short_id

    def __call__(self):
        self._write_run_attrs()
        self._init_package()
        self._upload_files()
        self._submit_job()
        self._write_lock()
        self._sync()

    def _write_run_attrs(self):
        self.run.write_attr("cloudml-job-name", self.job_name)
        self.run.write_attr("cloudml-job-dir", self.job_dir)

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

    def _upload_files(self):
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
        if self.args.package_path:
            args.extend(["--package-path", self.args.package_path])
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
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    def _apply_job_dir(self, args):
        def f(val):
            if os.path.exists(val):
                return os.path.join(self.job_dir, val)
            else:
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

class Deploy(object):

    def __init__(self, args, sdk):
        self.args = self._parse_args(args)
        self.run = plugin_util.current_run()
        self.deploying_run = _one_run(self.args.run)
        self.opref = opref.OpRef.from_run(self.deploying_run)
        self.model_name = self.args.model or self.opref.model_name
        self.safe_model_name = _safe_name(self.model_name)
        self.region = self.args.region or self._run_region() or DEFAULT_REGION
        self.model_version = self.args.version or self._model_version()
        self.sdk = sdk

    @staticmethod
    def _parse_args(args):
        p = argparse.ArgumentParser()
        p.add_argument("--run", required=True)
        p.add_argument("--version")
        p.add_argument("--region")
        p.add_argument("--bucket")
        p.add_argument("--model-binaries")
        p.add_argument("--model")
        p.add_argument("--runtime-version", default=DEFAULT_RUNTIME_VERSION)
        p.add_argument("--config")
        args, _ = p.parse_known_args(args)
        return args

    def _run_region(self):
        return self.deploying_run.get("flags", {}).get("region")

    @staticmethod
    def _model_version():
        return "v_%i" % time.time()

    def __call__(self):
        self._validate_args()
        self._ensure_model()
        self._create_version()

    def _validate_args(self):
        job_dir = self.deploying_run.get("cloudml-job-dir")
        if (not job_dir and
            not self.args.bucket and
            not self.args.model_binaries):
            cli.error(
                "missing required flags 'bucket' or 'model-binaries' (specifies "
                "where model binaries should be uploaded for deployment)")

    def _ensure_model(self):
        self.run.write_attr("cloudml-model-name", self.safe_model_name)
        args = [
            self.sdk.gcloud, "ml-engine", "models", "create",
            self.safe_model_name, "--regions", self.region
        ]
        cli.out("Creating model %s... " % self.safe_model_name, nl=False)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _out, err = p.communicate()
        if "model with the same name already exists" in err:
            cli.out("done (already created)")
        elif p.returncode == 0:
            cli.out("done")
        else:
            sys.stderr.write(err)
            sys.exit(p.returncode)

    def _create_version(self):
        model_binaries = self._ensure_model_binaries()
        self.run.write_attr("cloudml-model-binaries", model_binaries)
        self.run.write_attr("cloudml-model-version", self.model_version)
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
        job_dir = self.deploying_run.get("cloudml-job-dir")
        if not job_dir:
            return self._upload_model_binaries()
        else:
            return self._job_dir_model_binaries(job_dir)

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
        servo_path = os.path.join(self.deploying_run.path, "export", "Servo")
        timestamp_dirs = (
            sorted(os.listdir(servo_path), reverse=True)
            if os.path.exists(servo_path) else [])
        if not timestamp_dirs:
            cli.error(
                "cannot find model binaries in run %s "
                "(expected files under export/Servo)"
                % self.deploying_run.id)
        timestamp_dir = timestamp_dirs[0]
        if len(timestamp_dirs) > 1:
            log.warning(
                "found multiple timestamp directories under %s (assuming %s)",
                servo_path, timestamp_dir)
        return os.path.join(servo_path, timestamp_dir)

    def _remote_model_binaries(self, local_model_path):
        # Should be validated before we get here.
        assert self.args.bucket or self.args.model_binaries
        return self.args.model_binaries or (
            "gs://%s/guild_model_%s_%s" % (
                self.args.bucket,
                self.safe_model_name,
                os.path.basename(local_model_path)))

    def _job_dir_model_binaries(self, job_dir):
        servo_path = job_dir + "/export/Servo"
        try:
            out = subprocess.check_output([
                self.sdk.gsutil, "ls", servo_path])
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)
        else:
            paths = sorted(out.split("\n"), reverse=True)
            assert (len(paths) >= 2 and
                    paths[0] == "" and
                    paths[1].endswith("/Servo/")), paths
            timestamp_paths = paths[2:]
            if not timestamp_paths:
                cli.error(
                    "missing model binaries in %s" % servo_path)
            timestamp_path = timestamp_paths[0]
            if len(timestamp_paths) > 1:
                log.warning(
                    "found multiple timestamp paths under %s (assuming %s)",
                    servo_path, timestamp_path)
            return timestamp_path

class Predict(object):

    def __init__(self, args, sdk):
        self.args = self._parse_args(args)
        self.run = plugin_util.current_run()
        self.predicting_run = _one_run(self.args.run)
        self.sdk = sdk

    @staticmethod
    def _parse_args(args):
        p = argparse.ArgumentParser()
        p.add_argument("--run", required=True)
        p.add_argument("--instances", required=True)
        p.add_argument("--instance-type")
        p.add_argument("--format")
        args, _ = p.parse_known_args(args)
        return args

    def __call__(self):
        self._predict()

    def _predict(self):
        args = [self.sdk.gcloud]
        if self.args.format:
            args.extend(["--format", self.args.format])
        args.extend([
            "ml-engine", "predict",
            "--model", self._model_name(),
            "--version", self._model_version(),
        ])
        args.extend(self._instances_args())
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    def _model_name(self):
        val = self.predicting_run.get("cloudml-model-name")
        if not val:
            cli.error(
                "cannot predict with run %s: missing cloudml-model-name "
                "attribute" % self.predicting_run.short_id)
        return val

    def _model_version(self):
        val = self.predicting_run.get("cloudml-model-version")
        if not val:
            cli.error(
                "cannot predict with run %s: missing cloudml-model-version "
                "attribute" % self.predicting_run.short_id)
        return val

    def _instances_args(self):
        path = self.args.instances
        if not os.path.exists(path):
            cli.error("'%s' does not exist" % path)
        format = self.args.instance_type or self._instance_type_from_path(path)
        if format == "json":
            return ["--json-instances", path]
        elif format == "text":
            return ["--text-instances", path]
        else:
            cli.error("unsupported instance type '%s'" % format)

    @staticmethod
    def _instance_type_from_path(path):
        _, ext = os.path.splitext(path)
        return "json" if ext.lower() == ".json" else "text"

class CancelJob(object):

    def __init__(self, run, no_wait, sdk):
        self.run = run
        self.no_wait = no_wait
        self.sdk = sdk

    def __call__(self):
        job_name = self.run.get("cloudml-job-name")
        if not job_name:
            log.error(
                "cloudml-job-name not defined for run %s, cannot stop job",
                self.run.id)
            return
        self._cancel_job(job_name)
        if not self.no_wait:
            sync_run(self.run, watch=True)

    def _cancel_job(self, job_name):
        cli.out("Canceling %s" % job_name)
        args = [self.sdk.gcloud, "ml-engine", "jobs", "cancel", job_name]
        subprocess.call(args)

def _safe_name(s):
    return re.sub(r"[^0-9a-zA-Z]+", "_", s)

def _one_run(run_prefix):
    matches = list(var.find_runs(run_prefix))
    run_id, path = cmd_impl_support.one_run(matches, run_prefix)
    return guild.run.Run(run_id, path)

def _init_sdk():
    gsutil = util.which("gsutil")
    if not gsutil:
        cli.error(
            "cannot find required Google Cloud Storage utility 'gsutil'\n"
            "Refer to https://cloud.google.com/storage/docs/gsutil_install"
            " for more information.")
    gcloud = util.which("gcloud")
    if not gcloud:
        cli.error(
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

if __name__ == "__main__":
    assert len(sys.argv) >= 2, "missing command"
    op_name = sys.argv[1]
    op_args = sys.argv[2:]
    sdk = _init_sdk()
    if op_name == "train":
        op = Train(op_args, sdk)
    else:
        raise AssertionError(sys.argv)
    op()
