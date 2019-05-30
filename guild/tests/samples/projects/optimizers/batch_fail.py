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
