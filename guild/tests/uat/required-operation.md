# Required operation 1

These tets illustrate how Guild handles operation dependencies.

Use required-operation project.

    >>> cd(example("required-operation"))

Available operations:

    >>> run("guild ops")
    prepare-data  Prepare data for training
    train         Train a model on prepared data
    train2        Alternative train using different file layout
    <exit 0>

Delete runs in preparation for our tests.

    >>> quiet("guild runs rm -y")

Try to run `train` without a required run:

    >>> run("guild run train -y")
    WARNING: cannot find a suitable run for required resource 'prepared-data'
    Resolving prepared-data
    guild: run failed because a dependency was not met: could not resolve
    'prepared-data' in prepared-data resource: no suitable run for prepare-data
    <exit 1>

Run `prepare-data`:

    >>> run("guild run prepare-data -y")
    <exit 0>

Run `train` again:

    >>> run("guild run train -y")
    Resolving prepared-data
    Using run ... for prepared-data
    <exit 0>

Show runs:

    >>> run("guild runs")
    [1:...]  train         ...  completed  prepared-data=...
    [2:...]  prepare-data  ...  completed
    [3:...]  train              error
    <exit 0>

List files for latest `prepare-data` run:

    >>> run("guild ls -n -Fo prepare-data")
    README.md
    data1.txt
    guild.yml
    prepare_data.py
    subdir/
    subdir/data2.txt
    train2.py
    train.py

    >>> run("guild ls -n -Fo prepare-data --sourcecode")
    README.md
    guild.yml
    prepare_data.py
    train2.py
    train.py

    >>> run("guild ls -n -Fo prepare-data --dependencies")
    <exit 0>

    >>> run("guild ls -n -Fo prepare-data --generated")
    data1.txt
    subdir/data2.txt

Files for latest `train` run (use `-L` to traverse links:

    >>> run("guild ls -n -Fo train -L")
    README.md
    checkpoint.h5
    data/
    data/data1.txt
    data/subdir/
    data/subdir/data2.txt
    guild.yml
    model.json
    prepare_data.py
    train2.py
    train.py

    >>> run("guild ls -n -Fo train -L --sourcecode")
    README.md
    guild.yml
    prepare_data.py
    train2.py
    train.py

    >>> run("guild ls -n -Fo train -L --dependencies")
    data/data1.txt
    data/subdir/
    data/subdir/data2.txt

    >>> run("guild ls -n -Fo train -L --generated")
    checkpoint.h5
    model.json

Run prepare-data again. We want to show that Guild can select an older
run if needed.

    >>> quiet("guild run prepare-data -y")

And the data-prepare runs:

    >>> run("guild runs -Fo prepare-data")
    [1:...]  prepare-data  ...  completed
    [2:...]  prepare-data  ...  completed
    <exit 0>

Get the run ID for the original data prep:

    >>> data_prep_runs = gapi.runs_list(ops=["prepare-data"])
    >>> len(data_prep_runs)
    2
    >>> first_data_prep_run = data_prep_runs[1].id

Specify that `train` use the first data prep run:

    >>> run("guild run train prepared-data=%s -y" % first_data_prep_run)
    Resolving prepared-data
    Using run ... for prepared-data
    <exit 0>

Info for the latest train run, including dependencies:

    >>> run("guild runs info -d")
    id: ...
    operation: train
    from: .../guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: prepared-data=...
    sourcecode_digest: ...
    run_dir: ...
    command: ... -um guild.op_main train --
    exit_status: 0
    pid:
    tags:
    flags:
      prepared-data: ...
    scalars:
    dependencies:
      prepared-data:
        prepared-data:
          config: ...
          paths:
          - ../.../data1.txt
          - ../.../subdir
          uri: operation:prepare-data

Confirm that the latest train op used the data prep run we specified.

    >>> train_flags = gapi.runs_list()[0].get("flags")
    >>> train_flags["prepared-data"] == first_data_prep_run
    True

Run a batch where using the two prepared data runs.

First, the run IDs of the two prepare-data ops:

    >>> len(data_prep_runs)
    2
    >>> data_prep_1 = data_prep_runs[0].id
    >>> data_prep_2 = data_prep_runs[1].id

Run train using the two run IDs:

    >>> run("guild run train prepared-data=[%s,%s] -y"
    ...     % (data_prep_1, data_prep_2))
    INFO: [guild] Running trial ...: train (prepared-data=...)
    INFO: [guild] Resolving prepared-data
    INFO: [guild] Using run ... for prepared-data
    INFO: [guild] Running trial ...: train (prepared-data=...)
    INFO: [guild] Resolving prepared-data
    INFO: [guild] Using run ... for prepared-data
    <exit 0>

Verify train runs used the expected prepare runs:

    >>> train_runs = gapi.runs_list(ops=["train"])
    >>> train_runs[1].get("flags")["prepared-data"] == data_prep_1
    True
    >>> train_runs[0].get("flags")["prepared-data"] == data_prep_2
    True

Try again, but using an invalid run ID for one of the specified
prepared-data flag items. We use `--fail-on-trial-error` to highlight
the batch error.

    >>> run("guild run train prepared-data=[%s,xxx_invalid] "
    ...     "--fail-on-trial-error -y" % data_prep_1)
    INFO: [guild] Running trial ...: train (prepared-data=...)
    INFO: [guild] Resolving prepared-data
    INFO: [guild] Using run ... for prepared-data
    INFO: [guild] Running trial ...: train (prepared-data=xxx_invalid)
    INFO: [guild] Resolving prepared-data
    ERROR: [guild] Trial ... exited with an error: (1) run failed because a
    dependency was not met: could not resolve 'prepared-data' in prepared-data
    resource: no suitable run for prepare-data
    ERROR: [guild] Stopping batch because a trial failed (pending trials can
    be started as needed)
    <exit 1>
