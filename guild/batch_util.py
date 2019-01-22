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

import logging
import json
import os
import random
import re
import shutil
import sys

import six
from six.moves import shlex_quote

from guild import _api as gapi
from guild import cli
from guild import op_util
from guild import run as runlib
from guild import util
from guild import var

log = logging.getLogger("guild")

DEFAULT_MAX_TRIALS = 20

init_logging = op_util.init_logging

slice_function_pattern = re.compile(r"\[([^:]+):([^:]+)(?::(.+))?\]")
named_function_parts_pattern = re.compile(r"(\w+)\((.*?)\)")

class BatchError(Exception):
    pass

class MissingProtoError(BatchError):
    pass

class Trial(object):

    def __init__(self, batch, flags, run_id=None):
        self.batch = batch
        self.flags = flags
        self.run_id = run_id or runlib.mkid()
        self._trial_link = os.path.join(
            self.batch.batch_run.path, self.run_id)

    @property
    def initialized(self):
        return os.path.exists(self._trial_link)

    @property
    def run_deleted(self):
        return (
            os.path.exists(self._trial_link) and
            not os.path.exists(os.path.realpath(self._trial_link)))

    def init(self):
        if not os.path.exists(self._trial_link):
            trial_run = self._init_trial_run()
            self._make_trial_link(trial_run)
            self._write_batch_attr(trial_run)

    def _make_trial_link(self, trial_run):
        """Creates a link in batch run dir to trial."""
        rel_trial_path = os.path.relpath(
            trial_run.path, os.path.dirname(self._trial_link))
        os.symlink(rel_trial_path, self._trial_link)

    def _write_batch_attr(self, trial_run):
        """Writes the batch_run_id ID as batch attr of trial_run."""
        trial_run.write_attr("batch_run_id", self.batch.batch_run.id)

    def _init_trial_run(self):
        run_dir = os.path.join(var.runs_dir(), self.run_id)
        shutil.copytree(self.batch.proto_run.path, run_dir)
        run = runlib.Run(self.run_id, run_dir)
        run.write_attr("flags", self.flags)
        run.write_attr("label", " ".join(self._flag_assigns()))
        return run

    def _flag_assigns(self):
        def fmt(val):
            if isinstance(val, float):
                val = round(val, 4)
            return shlex_quote(op_util.format_flag_val(val))
        return [
            "%s=%s" % (name, fmt(self.flags[name]))
            for name in sorted(self.flags)
        ]

    def run(self):
        trial_run = self._initialized_trial_run()
        if not trial_run:
            raise RuntimeError("trial not initialized - needs call to init")
        opspec = trial_run.opref.to_opspec()
        log.info("Running %s (%s)", opspec, ", ".join(self._flag_assigns()))
        try:
            gapi.run(
                restart=trial_run.id,
                cwd=os.environ["CMD_DIR"],
                extra_env={"NO_RESTARTING_MSG": "1"})
        except gapi.RunError as e:
            sys.exit(e.returncode)
        except KeyboardInterrupt as e:
            sys.exit(-15)

    def _initialized_trial_run(self):
        if not os.path.exists(self._trial_link):
            return None
        run_dir = os.path.realpath(self._trial_link)
        run_id = os.path.basename(run_dir)
        return runlib.Run(run_id, run_dir)

class Batch(object):

    def __init__(self, batch_run):
        self.batch_run = batch_run
        self.proto_run = self._init_proto_run()
        self._proto_opdef_data = None
        self.trials = []

    def _init_proto_run(self):
        proto_path = self.batch_run.guild_path("proto")
        if not os.path.exists(proto_path):
            raise MissingProtoError(
                "missing operation proto in %s" % proto_path)
        return runlib.Run("", proto_path)

    @property
    def max_trials(self):
        return self.batch_run.get("_max_trials")

    @property
    def random_seed(self):
        return self.batch_run.get("_random_seed")

    @property
    def proto_opdef_data(self):
        if self._proto_opdef_data is None:
            opdef_data = self.proto_run.get_opdef_data({})
            if not isinstance(opdef_data, dict):
                log.warning(
                    "unexpected opdef data for %s: %r",
                    self.proto_run.id, opdef_data)
            self._proto_opdef_data = opdef_data
        return self._proto_opdef_data

    def gen_or_load_trials(self, gen_cb, default_max=DEFAULT_MAX_TRIALS):
        loaded = self._load_trials()
        if loaded is not None:
            self.trials = loaded
        else:
            self.trials = self.gen_trials(gen_cb, default_max)

    def _load_trials(self):
        path = self._trials_json_path()
        if not os.path.exists(path):
            return None
        data = json.load(open(path, "r"))
        return [
            Trial(self, trial_data["flags"], trial_data["run_id"])
            for trial_data in data]

    def _trials_json_path(self):
        return os.path.join(self.batch_run.path, "trials.json")

    def gen_trials(self, gen_cb, default_max=DEFAULT_MAX_TRIALS):
        all_trials = self._gen_all_trials(gen_cb)
        return self.sample_trials(all_trials, default_max)

    def _gen_all_trials(self, gen_cb):
        trials = []
        base_flags = self.proto_run.get("flags") or {}
        batches = self.proto_run.get("batches") or []
        if batches:
            trials = self._acc_batch_trials(base_flags, batches, gen_cb)
        else:
            trials = gen_cb(base_flags, self)
        return [Trial(self, flags) for flags in trials]

    def _acc_batch_trials(self, base_flags, batches, gen_cb):
        trials = []
        for batch_flags in batches:
            joined_flags = self._join_flags(base_flags, batch_flags)
            trials.extend(gen_cb(joined_flags, self))
        return trials

    @staticmethod
    def _join_flags(base, extra):
        joined = {}
        joined.update(base)
        joined.update(extra)
        return joined

    def sample_trials(self, trials, default_max=DEFAULT_MAX_TRIALS):
        max_trials = self.max_trials or default_max
        if len(trials) <= max_trials:
            return trials
        random.seed(self.random_seed)
        return random.sample(trials, max_trials)

    def init_and_run_trials(self):
        self.init_pending_trials()
        self.run_trials()

    def init_pending_trials(self):
        self._save_trials_json()
        for trial in self.trials:
            if not trial.initialized:
                trial.init()

    def _save_trials_json(self):
        data = [{
            "run_id": trial.run_id,
            "flags": trial.flags
        } for trial in self.trials]
        with open(self._trials_json_path(), "w") as f:
            json.dump(data, f)

    def run_trials(self):
        for trial in self.trials:
            if trial.run_deleted:
                assert trial.run_id
                log.info("trial %s deleted, skipping", trial.run_id)
            trial.run()

def default_main(gen_trials_cb):
    init_logging()
    try:
        batch = init_batch()
        batch.gen_or_load_trials(gen_trials_cb)
        if os.getenv("PRINT_TRIALS") == "1":
            print_trials(batch.trials)
        elif os.getenv("SAVE_TRIALS"):
            save_trials(batch.trials, os.getenv("SAVE_TRIALS"))
        else:
            batch.init_and_run_trials()
    except BatchError as e:
        op_util.exit(str(e))

def init_batch():
    return Batch(op_util.current_run())

def print_trials(trials):
    if trials:
        op_util.print_trials([t.flags for t in trials])

def save_trials(trials, path):
    if not trials:
        cli.out("Nothing to save")
        return
    cli.out("Saving %i trial(s) to %s" % (len(trials), path))
    op_util.save_trials([t.flags for t in trials], path)

def parse_function(s):
    if not isinstance(s, six.string_types):
        raise ValueError("requires string")
    return util.find_apply([
        _slice_function,
        _named_function,
        _not_a_function_error,
    ], s)

def _slice_function(s):
    m = slice_function_pattern.match(s)
    if not m:
        return None
    args_s = m.groups()
    if args_s[2] is None:
        args_s = args_s[0:2]
    args = [op_util.parse_arg_val(arg) for arg in args_s]
    return None, tuple(args)

def _named_function(s):
    parts_m = named_function_parts_pattern.match(s)
    if not parts_m:
        return None
    name, args_s = parts_m.groups()
    args = op_util.parse_arg_val("[%s]" % args_s)
    return name, tuple(args)

def _not_a_function_error(_s):
    raise ValueError("not a function")
