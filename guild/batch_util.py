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

import json
import logging
import os
import random
import sys
import time

from six.moves import shlex_quote

from guild import _api as gapi
from guild import cli
from guild import exit_code
from guild import op_util
from guild import run as runlib
from guild import util
from guild import var

log = logging.getLogger("guild")

DEFAULT_MAX_TRIALS = 20

init_logging = op_util.init_logging

class BatchError(Exception):
    pass

class MissingProtoError(BatchError):
    pass

###################################################################
# Default trial
###################################################################

class Trial(object):

    def __init__(self, batch, flags=None, run_id=None):
        self.batch = batch
        self.flags = flags
        self.run_id = run_id or runlib.mkid()
        self._trial_link = os.path.join(self.batch.batch_run.path, self.run_id)
        self._config_digest = self._init_config_digest()

    def _init_config_digest(self):
        if self.flags is None:
            return None
        return op_util.flags_hash(self.flags)

    def set_flags(self, flags):
        self.flags = flags
        self._config_digest = self._init_config_digest()

    def config_equals(self, trial):
        if self._config_digest is None:
            return False
        return self._config_digest == trial._config_digest

    def delete_pending_run(self):
        run = self.trial_run()
        if not run:
            return False
        if run.status == "pending":
            log.info("Deleting pending run %s (no longer needed)", run.id)
            util.safe_rmtree(run.path)
            if os.path.exists(self._trial_link):
                os.remove(self._trial_link)

    def trial_run(self, required=False):
        if not os.path.exists(self._trial_link):
            if required:
                raise RuntimeError("trial not initialized - needs call to init")
            return None
        run_dir = os.path.realpath(self._trial_link)
        run_id = os.path.basename(run_dir)
        return runlib.Run(run_id, run_dir)

    def init(self, run_dir=None, quiet=False):
        trial_run = self._init_trial_run(run_dir)
        self._make_trial_link(trial_run)
        if not quiet:
            log.info(
                "Initialized trial %s (%s)", self._run_desc(trial_run),
                ", ".join(self._flag_assigns()))

    def _init_trial_run(self, run_dir=None):
        run_dir = run_dir or os.path.join(var.runs_dir(), self.run_id)
        util.copytree(self.batch.proto_run.path, run_dir)
        run = runlib.Run(self.run_id, run_dir)
        run.write_attr("flags", self.flags)
        run.write_attr("label", self._default_label())
        run.write_attr("batch", self.batch.batch_run.id)
        return run

    def _default_label(self):
        opt_desc = self.batch.batch_run.get("label")
        if not opt_desc:
            opt_desc = self.batch.batch_run.opref.op_name
        flags = " ".join(self._flag_assigns())
        return "%s %s" % (opt_desc, flags)

    @staticmethod
    def _run_desc(run):
        return run.short_id or " in %s" % run.run_dir

    def _make_trial_link(self, trial_run):
        """Creates a link in batch run dir to trial."""
        rel_trial_path = os.path.relpath(
            trial_run.path, os.path.dirname(self._trial_link))
        util.ensure_deleted(self._trial_link)
        os.symlink(rel_trial_path, self._trial_link)

    def _flag_assigns(self):
        def fmt(val):
            if isinstance(val, float):
                val = round(val, 4)
            return shlex_quote(op_util.format_flag_val(val))
        return [
            "%s=%s" % (name, fmt(self.flags[name]))
            for name in sorted(self.flags)
        ]

    def run_needed(self):
        run = self.trial_run()
        if not run:
            return True
        return op_util.restart_needed(run, self.flags)

    def run(self, quiet=False, **kw):
        trial_run = self.trial_run(required=True)
        opspec = trial_run.opref.to_opspec()
        cwd = os.environ["CMD_DIR"]
        extra_env = {
            "NO_RESTARTING_MSG": "1"
        }
        if not quiet:
            log.info(
                "Running trial %s: %s (%s)", self._run_desc(trial_run),
                opspec, ", ".join(self._flag_assigns()))
        try:
            gapi.run(
                restart=trial_run.path,
                cwd=cwd,
                extra_env=extra_env,
                quiet=quiet,
                **kw)
        except gapi.RunError as e:
            op_util.ensure_exit_status(trial_run, e.returncode)
            log.error("Run %s failed - see logs for details", trial_run.id)
        except KeyboardInterrupt as e:
            sys.exit(exit_code.SIGTERM)

###################################################################
# Iter trial
###################################################################

class IterTrial(Trial):

    def __init__(self, init_trial_cb, batch, flags, run_dir=None):
        assert hasattr(batch, "_iter_trials_state")
        self.state = batch._iter_trials_state
        self.init_trial_cb = init_trial_cb
        super(IterTrial, self).__init__(batch, flags, run_dir)

    def init(self, *args, **kw):
        """Initialize an iter trial.

        We use `self.init_trial_cb` to perform additional trial
        initialization after the default init process.
        """
        flags = self.init_trial_cb(self, self.state)
        self.set_flags(flags)
        super(IterTrial, self).init(*args, **kw)

###################################################################
# Batch
###################################################################

class Batch(object):

    def __init__(self, batch_run, new_trial_cb=None):
        self.batch_run = batch_run
        self._new_trial_cb = new_trial_cb or Trial
        self.proto_run = self._init_proto_run()
        self._proto_opdef_data = None
        self._index_path = batch_run.guild_path("trials")
        self._needed = os.getenv("NEEDED_TRIALS_ONLY") == "1"

    def _init_proto_run(self):
        proto_path = self.batch_run.guild_path("proto")
        if not os.path.exists(proto_path):
            raise MissingProtoError(
                "missing operation proto in %s" % proto_path)
        return runlib.Run("", proto_path)

    @property
    def max_trials(self):
        return self.batch_run.get("max_trials")

    @property
    def random_seed(self):
        return self.batch_run.get("random_seed")

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
        return [self._new_trial_cb(self, flags) for flags in trials]

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

    def run_trials(self, trials, init_only=False):
        index = self.read_index(filter_existing=True)
        orphaned = self._remove_missing_trials(trials, index)
        self._delete_pending_trials(orphaned)
        self._add_new_trials(trials, index)
        self._write_index(index)
        for trial in index:
            if self._needed and not trial.run_needed():
                log.info(
                    "Skipping trial %s because flags have not "
                    "changed (--needed specified)", trial.run_id)
                continue
            trial.init()
            self._trial_init_wait_state()
            if not init_only:
                self._run_if_needed(trial)

    def read_index(self, filter_existing=False):
        if not os.path.exists(self._index_path):
            return []
        data = json.load(open(self._index_path, "r"))
        trials = [
            Trial(self, trial_data["flags"], trial_data["run_id"])
            for trial_data in data]
        if not filter_existing:
            return trials
        return [t for t in trials if self._trial_run_exists(t)]

    @staticmethod
    def _trial_run_exists(t):
        try:
            var.get_run(t.run_id)
        except LookupError:
            return False
        else:
            return True

    def _remove_missing_trials(self, trials, index):
        """Removes any trials in index that aren't in trials.

        Returns the list of removed trials.
        """
        removed = []
        index_copy = list(index)
        for trial in index_copy:
            if not self._in_trials(trial, trials):
                index.remove(trial)
                removed.append(trial)
        return removed

    @staticmethod
    def _in_trials(candidate, trials):
        return any((trial.config_equals(candidate) for trial in trials))

    @staticmethod
    def _delete_pending_trials(trials):
        for trial in trials:
            trial.delete_pending_run()

    @staticmethod
    def _sync_run_ids(index):
        for trial in index:
            if not trial.run_id:
                continue
            try:
                var.get_run(trial.run_id)
            except LookupError:
                # Trial run doesn't exist - generate a new ID
                trial.run_id = runlib.mkid()

    def _add_new_trials(self, source, target):
        for trial in source:
            if not self._in_trials(trial, target):
                target.append(trial)

    def _write_index(self, index):
        data = [{
            "run_id": trial.run_id,
            "flags": trial.flags
        } for trial in index]
        with open(self._index_path, "w") as f:
            json.dump(data, f)

    @staticmethod
    def _trial_init_wait_state():
        """Wait for a short period after initializing a trial.

        This wait state lets (non guaranteed but highlight likely)
        each trial directory get an incrementing mtime from the
        OS. This is used for (pseudo) deterministic sorting of
        generated trials using their run dir mtime attrs.
        """
        time.sleep(0.01)

    def _run_if_needed(self, trial):
        if self._needed and not trial.run_needed():
            log.debug("skipping trial %s", trial.run_id)
            return
        trial.run()

###################################################################
# Default main
###################################################################

def default_main(gen_trials_cb,
                 new_trial_cb=None,
                 default_max_trials=DEFAULT_MAX_TRIALS):
    init_logging()
    try:
        _default_main_impl(gen_trials_cb, default_max_trials, new_trial_cb)
    except BatchError as e:
        op_util.exit(str(e))

def _default_main_impl(gen_trials_cb, default_max_trials, new_trial_cb):
    batch = init_batch(new_trial_cb)
    trials = batch.gen_trials(gen_trials_cb, default_max_trials)
    if os.getenv("PRINT_TRIALS") == "1":
        print_trials(trials)
    elif os.getenv("SAVE_TRIALS"):
        save_trials(trials, os.getenv("SAVE_TRIALS"))
    elif os.getenv("PRINT_TRIALS_CMD") == "1":
        print_trials_cmd(trials)
    else:
        init_only = os.getenv("INIT_TRIALS_ONLY") == "1"
        batch.run_trials(trials, init_only)

def init_batch(new_trial_cb=None):
    return Batch(op_util.current_run(), new_trial_cb)

def print_trials(trials):
    if trials:
        op_util.print_trials([t.flags for t in trials])

def save_trials(trials, path):
    if not trials:
        cli.out("Nothing to save")
        return
    cli.out("Saving %i trial(s) to %s" % (len(trials), path))
    op_util.save_trials([t.flags for t in trials], path)

def print_trials_cmd(trials):
    for trial in trials:
        _print_trial_cmd(trial)

def _print_trial_cmd(trial):
    with util.TempDir("guild-trial-") as run_dir:
        trial.init(run_dir, quiet=True)
        trial.run(print_cmd=True, quiet=True)

###################################################################
# Iter trials main
###################################################################

def iter_trials_main(init_state_cb, init_trial_cb,
                     default_max_trials=DEFAULT_MAX_TRIALS):
    default_main(
        _gen_iter_trials_cb(init_state_cb, default_max_trials),
        _new_iter_trial_cb(init_trial_cb),
        default_max_trials)

def _gen_iter_trials_cb(init_state_cb, default_max_trials):
    def f(_flags, batch):
        batch._iter_trials_state = init_state_cb(batch)
        num_trials = batch.max_trials or default_max_trials
        return [None] * num_trials
    return f

def _new_iter_trial_cb(init_trial_cb):
    def f(batch, flags, run_id=None):
        return IterTrial(init_trial_cb, batch, flags, run_id)
    return f
