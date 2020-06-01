# Batch runs - skopt

These tests run each of the skopt based optimizers:

    - gp
    - forest
    - gbrt

We'll use the `noisy.py` script in the `optimizers` sample project.

    >>> project = Project(sample("projects", "optimizers"))

A helper to run an optimizer batch:

    >>> ignore_output = [
    ...     "The objective has been evaluated ",
    ... ]

    >>> def run(optimizer, x, trials, opt_flags=None):
    ...     project.run(
    ...         "noisy.py",
    ...         flags={"x": x},
    ...         opt_flags=opt_flags,
    ...         optimizer=optimizer,
    ...         max_trials=trials,
    ...         ignore_output=ignore_output)

We ignore messages from skopt that may be reasonably generated due to
random effects.

## Bayesian with gaussian process

Range without an initial value:

    >>> run("gp", "[-2.0:2.0]", 5)
    INFO: [guild] Random start for optimization (1 of 3)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...
    INFO: [guild] Random start for optimization (2 of 3)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...
    INFO: [guild] Random start for optimization (3 of 3)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...
    INFO: [guild] Found 3 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...
    INFO: [guild] Found 4 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...

Range with an initial value and opt flags:

    >>> with Env({"TRIAL_ENV": "1"}):
    ...     run("gp", "[-2.0:2.0:0.1]", 2, {"kappa": 1.5, "xi": 0.2})
    INFO: [guild] Random start for optimization (1 of 2)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=0.1)
    x: 0.100000
    noise: 0.1
    loss: ...
    INFO: [guild] Random start for optimization (2 of 2)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...

Range with a null value:

    >>> run("gp", None, 2)
    ERROR: [guild] flags for batch (noise=0.1, x=null) do not contain
    any search dimensions
    Try specifying a range for one or more flags as NAME=[MIN:MAX].
    <exit 1>

Our trials:

    >>> with Env({"TRIAL_ENV": "1"}):
    ...     project.print_runs(flags=True, status=True)
    noisy.py+gp  acq-func=gp_hedge kappa=1.96 noise=gaussian random-starts=3 xi=0.05  error
    noisy.py     noise=0.1 x=...                                                      completed
    noisy.py     noise=0.1 x=0.1                                                      completed
    noisy.py+gp  acq-func=gp_hedge kappa=1.5 noise=gaussian random-starts=3 xi=0.2    completed
    noisy.py     noise=0.1 x=...                                                      completed
    noisy.py     noise=0.1 x=...                                                      completed
    noisy.py     noise=0.1 x=...                                                      completed
    noisy.py     noise=0.1 x=...                                                      completed
    noisy.py     noise=0.1 x=...                                                      completed
    noisy.py+gp  acq-func=gp_hedge kappa=1.96 noise=gaussian random-starts=3 xi=0.05  completed

Cleanup for next tests:

    >>> project.delete_runs()
    Deleted 10 run(s)

## Forest

Range without an initial value:

    >>> with Env({"TRIAL_ENV": "1"}):
    ...     run("forest", "[-2.0:2.0]", 4)
    INFO: [guild] Random start for optimization (1 of 3)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...
    INFO: [guild] Random start for optimization (2 of 3)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...
    INFO: [guild] Random start for optimization (3 of 3)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...
    INFO: [guild] Found 3 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...

Range with an initial value and opt flags:

    >>> with Env({"TRIAL_ENV": "1"}):
    ...     run("forest", "[-2.0:2.0:0.3]", 2, {"kappa": 1.3, "xi": 0.3})
    INFO: [guild] Random start for optimization (1 of 2)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=0.3)
    x: 0.300000
    noise: 0.1
    loss: ...
    INFO: [guild] Random start for optimization (2 of 2)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...

Our trials:

    >>> project.print_runs(flags=True, status=True)
    noisy.py         noise=0.1 x=...                     completed
    noisy.py         noise=0.1 x=0.3                     completed
    noisy.py+forest  kappa=1.3 random-starts=3 xi=0.3    completed
    noisy.py         noise=0.1 x=...                     completed
    noisy.py         noise=0.1 x=...                     completed
    noisy.py         noise=0.1 x=...                     completed
    noisy.py         noise=0.1 x=...                     completed
    noisy.py+forest  kappa=1.96 random-starts=3 xi=0.05  completed

Cleanup for next tests:

    >>> project.delete_runs()
    Deleted 8 run(s)

## GBRT

Range without an initial value and an opt flag:

    >>> with Env({"TRIAL_ENV": "1"}):
    ...     run("gbrt", "[-2.0:2.0]", 3, {"random-starts": 2})
    INFO: [guild] Random start for optimization (1 of 2)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...
    INFO: [guild] Random start for optimization (2 of 2)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...
    INFO: [guild] Found 2 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...

Range with an initial value and opt flags:

    >>> with Env({"TRIAL_ENV": "1"}):
    ...     run("gbrt", "[-2.0:2.0:0.4]", 3, {"kappa": 1.4, "xi": 0.4})
    INFO: [guild] Random start for optimization (1 of 3)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=0.4)
    x: 0.400000
    noise: 0.1
    loss: ...
    INFO: [guild] Random start for optimization (2 of 3)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...
    INFO: [guild] Random start for optimization (3 of 3)
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=...)
    x: ...
    noise: 0.1
    loss: ...

Our trials:

    >>> project.print_runs(flags=True, status=True)
    noisy.py       noise=0.1 x=...                     completed
    noisy.py       noise=0.1 x=...                     completed
    noisy.py       noise=0.1 x=0.4                     completed
    noisy.py+gbrt  kappa=1.4 random-starts=3 xi=0.4    completed
    noisy.py       noise=0.1 x=...                     completed
    noisy.py       noise=0.1 x=...                     completed
    noisy.py       noise=0.1 x=...                     completed
    noisy.py+gbrt  kappa=1.96 random-starts=2 xi=0.05  completed
