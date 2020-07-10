import logging

from guild import batch_util
from guild import flag_util
from guild import index

import numpy as np
import hyperopt

DEFAULT_MAX_TRIALS = 20
DEFAULT_OBJECTIVE = "loss"

log = logging.getLogger()

prior_weight = 1.0
EI_candidates = 24
gamma = 0.25
startup_jobs = 20


def main():
    batch_util.init_logging()
    batch = batch_util.batch_run()
    batch_flags = batch.get("flags")
    max_trials = batch.get("max_trials") or DEFAULT_MAX_TRIALS
    random_seed = batch.get("random_seed")
    trials = hyperopt.Trials()
    try:
        hyperopt.fmin(
            fn=_objective_fn(batch),
            space=_space_for_flags(batch),
            algo=_tpe_suggest,
            max_evals=max_trials,
            show_progressbar=False,
            rstate=np.random.RandomState(random_seed),
            trials=trials,
        )
    except hyperopt.exceptions.AllTrialsFailed:
        pass
    else:
        _label_best(trials.best_trial)


def _objective_fn(batch):
    obj_scalar, obj_negate = batch_util.objective_scalar(batch)

    def fn(trial_flags):
        run = batch_util.run_trial(batch, trial_flags)
        obj_value = index.scalars(run).get(obj_scalar)
        if obj_value is None:
            log.error(
                "Trial %s did not log objective '%s' - cannot use to optimize",
                run.id,
                obj_scalar,
            )
            return {
                "status": hyperopt.STATUS_FAIL,
            }
        return {
            "status": hyperopt.STATUS_OK,
            "loss": obj_value * obj_negate,
            "run": run,
        }

    return fn


def _space_for_flags(batch):
    flags = batch.batch_proto.get("flags")
    return {name: _space_for_flag_val(val, name) for name, val in flags.items()}


def _space_for_flag_val(val, label):
    if isinstance(val, list):
        return hyperopt.hp.choice(label, val)
    else:
        try:
            func_name, func_args = flag_util.decode_flag_function(val)
        except ValueError:
            return hyperopt.hp.choice(label, [val])
        else:
            return _space_for_func(func_name, func_args, label, val)


def _space_for_func(func_name, func_args, flag_name, flag_val):
    func_name = func_name or "uniform"
    try:
        space_init = getattr(hyperopt.hp, func_name)
    except AttributeError:
        log.error("unsupported flag function used in %s=%s", flag_name, flag_val)
        raise SystemExit(1)
    else:
        try:
            space = space_init(flag_name, *func_args)
            hyperopt.pyll.stochastic.sample(space)
        except Exception as e:
            log.error("invalid flag function used in %s=%s: %s", flag_name, flag_val, e)
            raise SystemExit(1)
        else:
            return space


def _tpe_suggest(new_ids, domain, trials, seed):
    return hyperopt.tpe.suggest(
        new_ids,
        domain,
        trials,
        seed,
        prior_weight=prior_weight,
        n_startup_jobs=startup_jobs,
        n_EI_candidates=EI_candidates,
        gamma=gamma,
    )


def _label_best(trial):
    run = trial["result"]["run"]
    log.info("Labeling best run %s", run.id)
    run.write_attr("label", "best %s" % run.get("label"))


if __name__ == "__main__":
    main()
