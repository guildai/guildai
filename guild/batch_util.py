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
import sys

import six

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

    def __init__(self, batch, flags=None, run_id=None, attrs=None):
        self.batch = batch
        self.flags = flags
        self.run_id = run_id or runlib.mkid()
        self.attrs = attrs or {}

    def trial_run(self, required=False):
        trial_link = self._trial_link()
        if not os.path.exists(trial_link):
            if required:
                raise RuntimeError("trial not initialized - needs call to init")
            return None
        run_dir = os.path.realpath(trial_link)
        return runlib.Run(self.run_id, run_dir)

    def _trial_link(self):
        return os.path.join(self.batch.batch_run.path, self.run_id)

    def init(self, run_dir=None, quiet=False):
        trial_run = self._init_trial_run(run_dir)
        self._make_trial_link(trial_run)
        if not quiet:
            log.info(
                "Initialized trial %s (%s)",
                self._run_desc(trial_run),
                ", ".join(self._flag_assigns()))

    def _init_trial_run(self, run_dir=None):
        run_dir = run_dir or os.path.join(var.runs_dir(), self.run_id)
        run = runlib.Run(self.run_id, run_dir)
        if run.get("batch") != self.batch.batch_run.id:
            util.copytree(self.batch.proto_run.path, run_dir)
            run.write_attr("initialized", runlib.timestamp())
            for name, val in self.attrs.items():
                run.write_attr(name, val)
            assert isinstance(self.flags, dict)
            run.write_attr("flags", self.flags)
            if "label" not in self.attrs:
                run.write_attr("label", self.init_label())
            run.write_attr("batch", self.batch.batch_run.id)
        return run

    def init_label(self):
        parts = []
        opt_desc = self.batch.batch_run.get("label")
        if not opt_desc:
            opt_desc = self.batch_label()
        if opt_desc:
            parts.append(opt_desc)
        parts.append(" ".join(self._flag_assigns()))
        return " ".join(parts)

    def batch_label(self):
        batch_op_name = self.batch.batch_run.opref.op_name
        if batch_op_name == "+":
            return ""
        return batch_op_name

    @staticmethod
    def _run_desc(run):
        return run.short_id or " in %s" % run.run_dir

    def _make_trial_link(self, trial_run):
        """Creates a link in batch run dir to trial."""
        trial_link = self._trial_link()
        rel_trial_path = os.path.relpath(
            trial_run.path,
            os.path.dirname(trial_link))
        util.ensure_deleted(trial_link)
        os.symlink(rel_trial_path, trial_link)

    def _flag_assigns(self):
        return op_util.flag_assigns(self.flags)

    def run_needed(self):
        run = self.trial_run()
        if not run:
            return True
        return op_util.restart_needed(run, self.flags)

    def run(self, quiet=False, **kw):
        trial_run = self.trial_run(required=True)
        opspec = trial_run.opref.to_opspec()
        cwd = os.environ["CMD_DIR"]
        label = trial_run.get("label") or self.init_label()
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
                label=label,
                extra_env=extra_env,
                quiet=quiet,
                **kw)
        except gapi.RunError as e:
            op_util.ensure_exit_status(trial_run, e.returncode)
            log.error("Run %s failed - see logs for details", trial_run.id)
        except KeyboardInterrupt as e:
            sys.exit(exit_code.SIGTERM)

###################################################################
# Seq trial
###################################################################

class SeqTrial(Trial):
    """Variant of Trial used in sequential optimization.

    When optimizing in a sequence to take advantage of previous
    results to make better suggestions.
    """

    def __init__(self, init_trial_cb, batch, **kw):
        assert hasattr(batch, "_seq_trials_state")
        self.state = batch._seq_trials_state
        self.init_trial_cb = init_trial_cb
        super(SeqTrial, self).__init__(batch, **kw)

    def init(self, run_dir=None, quiet=False):
        """Initialize a sequential trial.

        We use `self.init_trial_cb` to perform additional trial
        initialization after the default init process.
        """
        result = self.init_trial_cb(self, self.state)
        assert isinstance(result, tuple) and len(result) == 2
        self.flags, self.attrs = result
        super(SeqTrial, self).init(run_dir, quiet)

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
        self.needed = os.getenv("NEEDED_TRIALS_ONLY") == "1"

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
        return [self._new_trial_cb(self, flags=flags) for flags in trials]

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
        trial_runs = [
            (run.id, run.get("flags"))
            for run in self.seq_trial_runs()
        ]
        for trial in trials:
            self._apply_existing_run_id(trial, trial_runs)
            trial.init()
            if init_only:
                continue
            if self.needed and not trial.run_needed():
                log.info(
                    "Skipping trial %s because flags have not "
                    "changed (--needed specified)", trial.run_id)
                continue
            trial.run()

    @staticmethod
    def _apply_existing_run_id(trial, trial_runs):
        if trial.flags is None:
            return
        for run_id, run_flags in trial_runs:
            if trial.flags == run_flags:
                trial.run_id = run_id
                break

    def seq_trial_runs(self, status=None):
        if isinstance(status, six.string_types):
            status = [status]
        batch_run_id = self.batch_run.id
        def filter(run):
            return (
                run.get("batch") == batch_run_id and
                (status is None or run.status in status))
        return var.runs(filter=filter)

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
# Seq trials main
###################################################################

def seq_trials_main(init_state_cb, init_trial_cb,
                     default_max_trials=DEFAULT_MAX_TRIALS):
    default_main(
        _gen_seq_trials_cb(init_state_cb, default_max_trials),
        _new_seq_trial_cb(init_trial_cb),
        default_max_trials)

def _gen_seq_trials_cb(init_state_cb, default_max_trials):
    def f(_flags, batch):
        batch._seq_trials_state = init_state_cb(batch)
        num_trials = batch.max_trials or default_max_trials
        return [None] * num_trials
    return f

def _new_seq_trial_cb(init_trial_cb):
    def f(batch, **kw):
        return SeqTrial(init_trial_cb, batch, **kw)
    return f
