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
