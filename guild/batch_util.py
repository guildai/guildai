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
import os
import random
import shutil
import sys

from six.moves import shlex_quote

from guild import _api as gapi
from guild import cli
from guild import op_util
from guild import run as runlib
from guild import var

log = logging.getLogger("guild")

DEFAULT_MAX_TRIALS = 20

init_logging = op_util.init_logging

class Trial(object):

    def __init__(self, batch, flags):
        self._batch = batch
        self._flags = flags
        self._run_id = runlib.mkid()
        self._trial_link = os.path.join(
            self._batch.batch_run.path, self._run_id)

    def _flag_assigns(self):
        format_val = lambda val: shlex_quote(op_util.format_flag_val(val))
        return [
            "%s=%s" % (name, format_val(self._flags[name]))
            for name in sorted(self._flags)
        ]

    @property
    def flags(self):
        return self._flags

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
            os.symlink(trial_run.path, self._trial_link)

    def _init_trial_run(self):
        run_dir = os.path.join(var.runs_dir(), self._run_id)
        shutil.copytree(self._batch.proto_run.path, run_dir)
        run = runlib.Run(self._run_id, run_dir)
        run.write_attr("flags", self._flags)
        run.write_attr("label", " ".join(self._flag_assigns()))
        return run

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

    def _init_proto_run(self):
        proto_path = self.batch_run.guild_path("proto")
        if not os.path.exists(proto_path):
            op_util.exit("missing operation proto in %s" % proto_path)
        return runlib.Run("", proto_path)

    @property
    def max_trials(self):
        return self.batch_run.get("_max_trials")

    @property
    def random_seed(self):
        return self.batch_run.get("_random_seed")

    def gen_trials(self, gen_trials_cb, default_max=DEFAULT_MAX_TRIALS):
        all_trials = self._gen_all_trials(gen_trials_cb)
        return self.sample_trials(all_trials, default_max)

    def _gen_all_trials(self, gen_trials_cb):
        trials = []
        base_flags = self.proto_run.get("flags") or {}
        batches = self.proto_run.get("batches") or []
        if batches:
            trials = self._acc_batch_trials(base_flags, batches, gen_trials_cb)
        else:
            trials = gen_trials_cb(base_flags, self)
        return [Trial(self, flags) for flags in trials]

    def _acc_batch_trials(self, base_flags, batches, gen_trials_cb):
        trials = []
        for batch_flags in batches:
            joined_flags = self._join_flags(base_flags, batch_flags)
            trials.extend(gen_trials_cb(joined_flags, self))
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

def init_batch():
    return Batch(op_util.current_run())

def default_main(gen_trials_cb):
    init_logging()
    batch = init_batch()
    trials = batch.gen_trials(gen_trials_cb)
    if os.getenv("PRINT_TRIALS") == "1":
        print_trials(trials)
    elif os.getenv("SAVE_TRIALS"):
        save_trials(trials, os.getenv("SAVE_TRIALS"))
    else:
        init_pending_trials(trials)
        run_trials(trials)

def print_trials(trials):
    if trials:
        op_util.print_trials([t.flags for t in trials])

def save_trials(trials, path):
    if not trials:
        cli.out("Nothing to save")
        return
    cli.out("Saving %i trial(s) to %s" % (len(trials), path))
    op_util.save_trials([t.flags for t in trials], path)

def init_pending_trials(trials):
    for trial in trials:
        if not trial.initialized:
            trial.init()

def run_trials(trials):
    for trial in trials:
        if trial.run_deleted:
            assert trials.run_id
            log.info("trial %s deleted, skipping", trial.run_id)
        trial.run()
