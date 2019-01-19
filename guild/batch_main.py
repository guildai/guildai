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

import itertools
import logging
import random
import os
import shutil
import sys

from six.moves import shlex_quote

from guild import _api as gapi
from guild import op_util
from guild import run as runlib
from guild import var

log = logging.getLogger("guild")

DEFAULT_MAX_TRIALS = 100

class Trial(object):

    def __init__(self, batch_run, proto, flags):
        self._batch_run = batch_run
        self._proto = proto
        self._flags = flags
        self._run_id = runlib.mkid()
        self._trial_link = os.path.join(self._batch_run.path, self._run_id)

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
        shutil.copytree(self._proto.path, run_dir)
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

def main():
    op_util.init_logging()
    batch_run = op_util.current_run()
    proto = _batch_proto(batch_run)
    all_trials = _all_trials(batch_run, proto)
    trials = _sample_trials(all_trials, batch_run)
    if os.getenv("PRINT_TRIALS") == "1":
        _print_trials(trials)
    else:
        _init_pending(trials)
        _run(trials)

def _batch_proto(batch_run):
    proto_path = batch_run.guild_path("proto")
    if not os.path.exists(proto_path):
        op_util.exit("missing operation proto in %s" % proto_path)
    return runlib.Run("", proto_path)

def _all_trials(batch_run, proto):
    trials = []
    base_flags = proto.get("flags") or {}
    batches = proto.get("batches") or []
    if batches:
        _acc_batch_trials(base_flags, batches, trials)
    else:
        _acc_trials(base_flags, trials)
    return [Trial(batch_run, proto, dict(flags)) for flags in trials]

def _acc_batch_trials(base_flags, batches, trials):
    for batch_flags in batches:
        _acc_trials(_join_flags(base_flags, batch_flags), trials)

def _join_flags(base, extra):
    joined = {}
    joined.update(base)
    joined.update(extra)
    return joined

def _acc_trials(flags, trials):
    flag_list = [
        _trial_flags(name, val)
        for name, val in sorted(flags.items())]
    for trial in itertools.product(*flag_list):
        trials.append(trial)

def _trial_flags(flag_name, flag_val):
    if isinstance(flag_val, list):
        return [(flag_name, trial_val) for trial_val in flag_val]
    return [(flag_name, flag_val)]

def _sample_trials(trials, batch_run):
    max_trials = batch_run.get("_max_trials", DEFAULT_MAX_TRIALS)
    if len(trials) <= max_trials:
        return trials
    random_seed = batch_run.get("_random_seed")
    random.seed(random_seed)
    return random.sample(trials, max_trials)

def _print_trials(trials):
    op_util.print_trials([t.flags for t in trials])

def _init_pending(trials):
    for trial in trials:
        if not trial.initialized:
            trial.init()

def _run(trials):
    for trial in trials:
        if trial.run_deleted:
            assert trials.run_id
            log.info("trial %s deleted, skipping", trial.run_id)
        trial.run()

if __name__ == "__main__":
    main()
