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
import os

import guild.run

from guild import op_util

class Trial(object):

    def __init__(self, batch_run, proto, flags):
        self._batch_run = batch_run
        self._proto = proto
        self._flags = flags
        self._hash = self._init_flags_hash()
        self._hash_path = self._init_hash_path()

    def _init_flags_hash(self):
        # Hash of sorted flag values
        parts = []
        for name in sorted(self._flags):
            parts.extend([name, str(self._flags[name])])
        return hashlib.md5("\n".join(parts)).hexdigest()

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
            op = self._init_op()
            #run = op.init()
            #self._make_hash_path(run.path)

    def _init_op(self):
        print("TODO: init yo")

    def _make_hash_path(self, run_dir):
        util.ensure_dir(os.path.dirname(self._hash_path))
        os.symlink(run_dir, self._hash_path)

    def run(self):
        print("TODO: run yo")

    """

    def _init_trials(proto, config):
        trials = []
        for flags in config:
            trial_op = _trial_op(proto, flags)
            trials.append(trial_op)
            trial_hash = _trial_hash(flags)
            trial_run_dir = _trial_run_id(trial_hash)
            if not
            if not _trial_hash_exists(trial_hash):
                run = trial_op.init()
                _write_trial_hash(trial_hash, run.path)
        return trials

    def _trial_op(proto, flags):
        pass

    def _trial_hash_exists(hash):
        return os.path.exists(_trial_hash_path(hash))

    def _trial_hash_path(hash):
        run = op_util.current_run()
        return os.path.join(run.path, hash)

    def _write_trial_hash

    def _run_trials(trials):
        pass
    """


def main():
    batch_run = op_util.current_run()
    proto = _batch_proto(batch_run)
    trials = _init_trials(batch_run, proto)
    _init_pending(trials)
    _run(trials)

def _batch_proto(batch_run):
    proto_path = batch_run.guild_path("proto")
    if not os.path.exists(proto_path):
        op_util.exit("missing operation proto in %s" % proto_path)
    return guild.run.Run("", proto_path)

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
        for name, val in flags.items()]
    for trial in itertools.product(*flag_list):
        trials.append(trial)

def _trial_flags(flag_name, flag_val):
    if isinstance(flag_val, list):
        return [(flag_name, trial_val) for trial_val in flag_val]
    return [(flag_name, flag_val)]

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

"""

def _init_trial_ops(self):
    for trial_op in self._trial_ops():
        trial_hash = self._trial_hash(trial_op)
        if not self._trial_hash_exists(trial_hash):
            trial_run = trial_op.init()
            self._write_trial_hash(trial_hash, trial_run.id)

def _trial_ops(self):
    return [
        TrialOp(self.child_op, trial_flags)
        for trial_flags in self.trials]


def _trial_hash_exists(self, trial_hash):
    return os.path.exists(self._trial_hash_path(trial_hash))

def _trial_hash_path(self, trial_hash):
    return os.path.join(self._run.guild_path("trials"), trial_hash)

def _write_trial_hash(self, trial_hash, run_id):
    path = self._trial_hash_path(trial_hash)
    util.ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        f.write(run_id)

class TrialOp(op.Operation):

    def __init__(self, child_op, trial_flags):
        super(TrialOp, self).__init__(
            opref=child_op.opref,
            opdef=self._trial_opdef(child_op, trial_flags),
            run_dir=child_op.run_dir,
            resource_config=child_op.resource_config,
            extra_attrs=child_op.extra_attrs,
            stage_only=child_op.stage_only,
            gpus=child_op.gpus)

    @staticmethod
    def _trial_opdef(child_op, trial_flags):
        trial_opdef = copy.deepcopy(child_op.opdef)
        for name, val in trial_flags.items():
            trial_opdef.set_flag_value(name, val)
        return trial_opdef

def _trial_run_for_hash(trial_hash):
    path = self._trial_hash_path(trial_hash)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        run_dir = f.read()
    run_id = os.path.basename(run_dir)
    return runlib.Run(run_id, run_dir)

# self.trials = self._init_trials(batch_files)

"""

if __name__ == "__main__":
    main()
