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

import hashlib
import itertools
import logging
import os
import shutil
import sys

from six.moves import shlex_quote

from guild import _api as gapi
from guild import op_util
from guild import run as runlib
from guild import util
from guild import var

log = logging.getLogger("guild")

class Trial(object):

    def __init__(self, batch_run, proto, flags):
        self._batch_run = batch_run
        self._proto = proto
        self._flags = flags
        self._hash = self._init_flags_hash()
        self._hash_path = self._init_hash_path()

    @property
    def flags(self):
        return self._flags

    def _init_flags_hash(self):
        # Hash of sorted flag values
        parts = []
        for name in sorted(self._flags):
            parts.extend([name, ":", str(self._flags[name])])
        joined_flags = "\n".join(parts).encode()
        return hashlib.md5(joined_flags).hexdigest()

    def _init_hash_path(self):
        hashes_dir = self._batch_run.guild_path("hashes")
        return os.path.join(hashes_dir, self._hash)

    @property
    def initialized(self):
        return os.path.exists(self._hash_path)

    @property
    def run_deleted(self):
        return (
            os.path.exists(self._hash_path) and
            not os.path.exists(os.path.realpath(self._hash_path)))

    def init(self):
        if not os.path.exists(self._hash_path):
            trial_run = self._init_trial_run()
            self._write_hash_path(trial_run.path)

    def _init_trial_run(self):
        run_id = runlib.mkid()
        run_dir = os.path.join(var.runs_dir(), run_id)
        shutil.copytree(self._proto.path, run_dir)
        run = runlib.Run(run_id, run_dir)
        run.write_attr("flags", self._flags)
        return run

    def _write_hash_path(self, run_dir):
        util.ensure_dir(os.path.dirname(self._hash_path))
        os.symlink(run_dir, self._hash_path)

    def run(self):
        trial_run = self._initialized_trial_run()
        if not trial_run:
            raise RuntimeError("trial not initialized - needs call to init")
        opspec = trial_run.opref.to_opspec()
        flags = _run_flag_assigns(trial_run)
        log.info("Running %s (%s)", opspec, ", ".join(flags))
        try:
            gapi.run(
                restart=trial_run.id,
                label=" ".join(flags),
                cwd=os.environ["CMD_DIR"],
                extra_env={"NO_RESTARTING_MSG": "1"})
        except gapi.RunError as e:
            sys.exit(e.returncode)

    def _initialized_trial_run(self):
        if not os.path.exists(self._hash_path):
            return None
        run_dir = os.path.realpath(self._hash_path)
        run_id = os.path.basename(run_dir)
        return runlib.Run(run_id, run_dir)

def _run_flag_assigns(run):
    flags = run.get("flags", {})
    return [
        "%s=%s" % (name, _format_flag_val(flags[name]))
        for name in sorted(flags)
    ]

def _format_flag_val(val):
    return shlex_quote(op_util.format_flag_val(val))

def main():
    op_util.init_logging()
    batch_run = op_util.current_run()
    proto = _batch_proto(batch_run)
    trials = _init_trials(batch_run, proto)
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

def _init_trials(batch_run, proto):
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
