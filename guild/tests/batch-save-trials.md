# Saving batch trials

Batch trials can be saved to a CSV file via the `run` command using
the `save_trial` option.

We'll use the `optimizers` project to illustrate.

    >>> project = Project(sample("projects", "optimizers"))

Let's create a directory to save our trials in.

    >>> save_dir = mkdtemp()
    >>> dest_path = path(save_dir, "trials.csv")

Let's run with a set of flags and the `save_trials` flag.

    >>> project.run(
    ...     "echo.py",
    ...     flags={"x": [1.1, 2.2], "y": [1, 2], "z": ["b"]},
    ...     save_trials=dest_path)
    Saving 4 trial(s) to .../trials.csv

The contents of our save directory:

    >>> find(save_dir)
    trials.csv

And the trials file:

    >>> cat(dest_path)
    x,y,z
    1.1,1,b
    1.1,2,b
    2.2,1,b
    2.2,2,b

We can use the trials file to run a batch.

    >>> project.run("echo.py", batch_files=[dest_path])
    INFO: [guild] Initialized trial ... (x=1.1, y=1, z=b)
    INFO: [guild] Running trial ...: echo.py (x=1.1, y=1, z=b)
    1.1 1 'b'
    INFO: [guild] Initialized trial ... (x=1.1, y=2, z=b)
    INFO: [guild] Running trial ...: echo.py (x=1.1, y=2, z=b)
    1.1 2 'b'
    INFO: [guild] Initialized trial ... (x=2.2, y=1, z=b)
    INFO: [guild] Running trial ...: echo.py (x=2.2, y=1, z=b)
    2.2 1 'b'
    INFO: [guild] Initialized trial ... (x=2.2, y=2, z=b)
    INFO: [guild] Running trial ...: echo.py (x=2.2, y=2, z=b)
    2.2 2 'b'
