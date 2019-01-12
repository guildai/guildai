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

def main():

    print("Yop")

"""
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
"""

# self.trials = self._init_trials(batch_files)

"""
def _init_trials(self, batch_files):
    trials = []
    base_flags = self.child_op.flag_vals
    if batch_files:
        self._acc_batch_file_trials(base_flags, batch_files, trials)
    else:
        self._acc_trials(base_flags, trials)
    return [dict(trial_flags) for trial_flags in trials]

def _acc_batch_file_trials(self, base_flags, batch_files, trials):
    for batch_file in batch_files:
        for batch_file_flags in self._iter_batch_file_flags(batch_file):
            self._acc_trials(
                self._join_flags(base_flags, batch_file_flags),
                trials)

@staticmethod
def _join_flags(base, extra):
    joined = {}
    joined.update(base)
    joined.update(extra)
    return joined

def _iter_batch_file_flags(self, batch_file):
    iterator = self._iterator_for_batch_file(batch_file)
    for flags in iterator:
        yield flags

@staticmethod
def _iterator_for_batch_file(batch_file):
    ext = os.path.splitext(batch_file)[1].lower()
    if ext in (".json", ".yml", ".yaml"):
        return YAMLFlags(batch_file)
    elif ext in (".csv",):
        return CSVFlags(batch_file)
    else:
        raise BatchError(
            "unsupported batch file extension for %s"
            % batch_file)

def _acc_trials(self, flags, trials):
    flag_list = [
        self._trial_flags(name, val)
        for name, val in flags.items()]
    for trial in itertools.product(*flag_list):
        trials.append(trial)

@staticmethod
def _trial_flags(flag_name, flag_val):
    if isinstance(flag_val, list):
        return [(flag_name, trial_val) for trial_val in flag_val]
    return [(flag_name, flag_val)]

"""


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

@staticmethod
def _trial_hash(trial_op):
    # Hash uses op ref and sorted flag values
    parts = [str(trial_op.opref)]
    for name in sorted(trial_op.flag_vals):
        parts.extend([name, str(trial_op.flag_vals[name])])
    return hashlib.md5("\n".join(parts)).hexdigest()

def _trial_hash_exists(self, trial_hash):
    return os.path.exists(self._trial_hash_path(trial_hash))

def _trial_hash_path(self, trial_hash):
    return os.path.join(self._run.guild_path("trials"), trial_hash)

def _write_trial_hash(self, trial_hash, run_id):
    path = self._trial_hash_path(trial_hash)
    util.ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        f.write(run_id)
"""


def _trial_run_for_hash(trial_hash):
    path = self._trial_hash_path(trial_hash)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        run_dir = f.read()
    run_id = os.path.basename(run_dir)
    return runlib.Run(run_id, run_dir)

class YAMLFlags(object):

    def __init__(self, path):
        self._data = yaml.load(open(path, "r"))
        if not isinstance(self._data, list):
            raise BatchError(
                "unsupported data type for batch file %s: %s"
                % (path, type(self._data)))
        for item in self._data:
            if not isinstance(item, dict):
                raise BatchError(
                    "supported data for batch file %s trial: %r"
                    % item)

    def __iter__(self):
        for item in self._data:
            yield item

class CSVFlags(object):

    def __init__(self, path):
        self._reader = csv.reader(open(path, "r"))
        try:
            self._flag_names = next(self._reader)
        except StopIteration:
            self._flag_names = None

    def __iter__(self):
        if self._flag_names:
            for row in self._reader:
                yield dict(zip(self._flag_names, row))

if __name__ == "__main__":
    main()
