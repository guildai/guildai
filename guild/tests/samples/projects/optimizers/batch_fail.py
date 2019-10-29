"""
import sys

from guild import batch_util

batch_fail = False
trials_fail = ""

def init_state(batch):
    return batch_util.SeqState(
        batch,
        trial=0,
        trials_fail=_trials_fail())

def _trials_fail():
    return [int(s) for s in str(trials_fail).split(",") if s]

def init_trial(trial, state):
    flags = {}
    flags.update(state.proto_flags)
    if state.trial in state.trials_fail:
        if batch_fail:
            print("BATCH FAIL")
            sys.exit(1)
        flags["fail"] = True
    state.trial += 1
    return flags, {}

batch_util.seq_trials_main(init_trial, init_state)
"""
from guild import batch_util

# Flags
max_trials = 5
batch_fail = False
trials_fail = ""

batch_run = batch_util.batch_run()
proto_flags = batch_run.batch_proto.get("flags") or {}
trials_count = batch_run.get("max_trials") or max_trials
trials_fail_list = [int(s) for s in str(trials_fail).split(",") if s]

for i in range(trials_count):
    trial_flags = dict(proto_flags)
    trial_flags["fail"] = (i + 1) in trials_fail_list
    try:
        batch_util.run_trial(batch_run, trial_flags)
    except SystemExit as e:
        if batch_fail:
            print("BATCH FAIL")
            raise SystemExit(2)
