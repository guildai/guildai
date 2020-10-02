# Saving batch trials

Batch trials can be saved to a CSV file via the `run` command using
the `save_trial` option.

We'll use the `optimizers` project to illustrate.

    >>> project = Project(sample("projects", "optimizers"))

Let's create a directory to save our trials in.

    >>> save_dir = mkdtemp()

## CSV Format

    >>> csv_path = path(save_dir, "trials.csv")

Run with a set of flags and the `save_trials` flag.

    >>> project.run(
    ...     "echo.py",
    ...     flags={"x": [1.1], "y": [1], "z": ["b", "1", "a a"]},
    ...     save_trials=csv_path)
    Saving trials to .../trials.csv

The contents of our save directory:

    >>> find(save_dir)
    trials.csv

And the trials file:

    >>> cat(csv_path)
    x,y,z
    1.1,1,b
    1.1,1,'1'
    1.1,1,a a

Use the trials file to run a batch.

    >>> project.run("echo.py", batch_files=[csv_path])
    INFO: [guild] Running trial ...: echo.py (x=1.1, y=1, z=b)
    1.1 1 'b'
    INFO: [guild] Running trial ...: echo.py (x=1.1, y=1, z='1')
    1.1 1 '1'
    INFO: [guild] Running trial ...: echo.py (x=1.1, y=1, z='a a')
    1.1 1 'a a'

## JSON Format

    >>> json_path = path(save_dir, "trials.json")

Save trials.

    >>> project.run(
    ...     "echo.py",
    ...     flags={"x": [1.1], "y": [1], "z": ["b", "1", "a a"]},
    ...     save_trials=json_path)
    Saving trials to .../trials.json

The contents of our save directory:

    >>> find(save_dir)
    trials.csv
    trials.json

And the trials file:

    >>> cat(json_path)
    [{"x": 1.1, "y": 1, "z": "b"},
     {"x": 1.1, "y": 1, "z": "1"},
     {"x": 1.1, "y": 1, "z": "a a"}]

Use the trials file to run a batch.

    >>> project.run("echo.py", batch_files=[json_path])
    INFO: [guild] Running trial ...: echo.py (x=1.1, y=1, z=b)
    1.1 1 'b'
    INFO: [guild] Running trial ...: echo.py (x=1.1, y=1, z='1')
    1.1 1 '1'
    INFO: [guild] Running trial ...: echo.py (x=1.1, y=1, z='a a')
    1.1 1 'a a'

## CSV Format - No Extension

    >>> noext_path = path(save_dir, "trials")

Save trials.

    >>> project.run("echo.py", flags={"x": [1]}, save_trials=noext_path)
    Saving trials to .../trials

The contents of our save directory:

    >>> find(save_dir)
    trials
    trials.csv
    trials.json

And the trials file:

    >>> cat(noext_path)
    x,y,z
    1,2,a

Use the trials file to run a batch.

    >>> project.run("echo.py", batch_files=[noext_path])
    1 2 'a'

## Unsupported Format

    >>> other_path = path(save_dir, "trials.xxx")

Save trials.

    >>> project.run("echo.py", flags={"x": [1]}, save_trials=other_path)
    guild: Unsupported extension '.xxx' - use '.csv', '.json', or no extension
    <exit 1>
