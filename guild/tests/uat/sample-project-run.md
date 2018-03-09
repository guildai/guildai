# Default project run

After training the sample project, we can list its runs:

    >>> run("guild -C sample-project runs list")
    Limiting runs to 'sample-project' (use --all to include all)
    [0:...]  ./sample-project:train  ... ...  completed
    <exit 0>

And get info and files for the run:

    >>> run("guild -C sample-project runs info --files")
    Limiting runs to 'sample-project' (use --all to include all)
    id: ...
    operation: ./sample-project:train
    status: completed
    started: ...
    stopped: ...
    run_dir: ...
    command: ... -um guild.op_main train --batch-size 64 --epochs 5 --learning-rate 0.01
    exit_status: 0
    pid:
    files:
      data.csv
    <exit 0>
