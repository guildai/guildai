# Batch random optimizer

    >>> project = Project(sample("projects", "optimizers"))

Helper to print flag value results:

    >>> def unique_vals(runs):
    ...     vals = {}
    ...     for run in runs:
    ...         for name, val in run.get("flags").items():
    ...             seen = vals.get(name)
    ...             if seen is None:
    ...                 vals[name] = val
    ...             elif seen != "<multiple>" and seen != val:
    ...                 vals[name] = "<multiple>"
    ...     pprint(vals)

## Explicit optimizer

### No search dimensions

An operation must contain at least one search dimension, otherwise
Guild exits with an error.

    >>> project.run("echo.py", optimizer="random")
    ERROR: [guild] flags for batch (x=1.0, y=2, z=a) do not contain any
    search dimensions
    Try specifying a range for one or more flags as NAME=[MIN:MAX].
    <exit 1>

    >>> project.delete_runs()
    Deleted 1 run(s)

### Search over one flag

Run three trials with a search over `x`.

    >>> project.run("echo.py", optimizer="random", max_trials=3,
    ...             flags={"x": "[1:100]"})
    INFO: [guild] Running trial ...: echo.py (x=..., y=2, z=a)
    ... 2 'a'
    INFO: [guild] Running trial ...: echo.py (x=..., y=2, z=a)
    ... 2 'a'
    INFO: [guild] Running trial ...: echo.py (x=..., y=2, z=a)
    ... 2 'a'

    >>> runs = project.list_runs()
    >>> len(runs)
    4

The first run is the batch.

    >>> runs[-1].opref.to_opspec()
    'skopt:random'

The other runs are the trials.

    >>> trials = runs[:-1]
    >>> list(set([trial.opref.to_opspec(project.cwd) for trial in trials]))
    ['echo.py']

View unique values for the other runs.

    >>> unique_vals(trials)
    {'x': '<multiple>', 'y': 2, 'z': 'a'}

    >>> project.delete_runs()
    Deleted 4 run(s)

### Search over all flags

Run five trials with search over all flags.

    >>> project.run("echo.py", optimizer="random", max_trials=10,
    ...             flags={"x": "[1:100]",
    ...                    "y": "[-99.99:99.99]",
    ...                    "z": ["a", "b", "c"]})
    INFO: [guild] Running trial ...: echo.py (...)
    ...

    >>> runs = project.list_runs()
    >>> len(runs)
    11

The first run is the batch.

    >>> runs[-1].opref.to_opspec()
    'skopt:random'

The other runs are the trials.

    >>> trials = runs[:-1]
    >>> list(set([trial.opref.to_opspec(project.cwd) for trial in trials]))
    ['echo.py']

View unique values for the other runs.

    >>> unique_vals(trials)
    {'x': '<multiple>', 'y': '<multiple>', 'z': '<multiple>'}

    >>> project.delete_runs()
    Deleted 11 run(s)

## Implicit random optimizer

If an operation is run with one or more random distribution values,
Guild applies the random optimizer if one is not explicitly provided
by the user.

Uniform distribution short form:

    >>> project.run("echo.py", flags={"x": "[1:10]"}, max_trials=5)
    INFO: [guild] Running trial ...
    INFO: [guild] Running trial ...
    INFO: [guild] Running trial ...
    INFO: [guild] Running trial ...
    INFO: [guild] Running trial ...

    >>> runs = project.list_runs()
    >>> runs[-1].opref.to_opspec()
    'skopt:random'

    >>> trials = runs[:-1]
    >>> unique_vals(trials)
    {'x': '<multiple>', 'y': 2, 'z': 'a'}

`uniform` function:

    >>> project.run("echo.py", flags={"x": "uniform[1:10]"}, max_trials=1)
    INFO: [guild] Running trial ...

    >>> runs = project.list_runs()
    >>> runs[0].opref.to_opspec(project.cwd)
    'echo.py'

    >>> runs[1].opref.to_opspec()
    'skopt:random'

`loguniform` function:

    >>> project.run("echo.py", flags={"x": "loguniform[1:10]"}, max_trials=1)
    INFO: [guild] Running trial ...

    >>> runs = project.list_runs()
    >>> runs[0].opref.to_opspec(project.cwd)
    'echo.py'

    >>> runs[1].opref.to_opspec()
    'skopt:random'


## Errors and warnings

Specifying --max-trials for a normal run:

    >>> project.run("echo.py", max_trials=5)
    WARNING: not a batch run - ignoring --max-trials
    1.0 2 'a'

Invalid flag function:

    >>> project.run("echo.py", flags={"x": "floop[1:10]"})
    ERROR: [guild] unknown function 'floop' used for flag x
    <exit 1>

Too many arguments to uniform function:

    >>> project.run("echo.py", flags={"x": "[1:2:3:4]"})
    ERROR: [guild] uniform requires 2 or 3 args, got (1, 2, 3, 4) for flag x
    <exit 1>

Too many arguments to loguniform function:

    >>> project.run("echo.py", flags={"x": "loguniform[1:2:3:4]"})
    ERROR: [guild] loguniform requires 2 or 3 args, got (1, 2, 3, 4) for flag x
    <exit 1>
