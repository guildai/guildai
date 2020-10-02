# Run With Proto

Runs can be started using settings from other runs. These other runs
are called prototypes and are specified for the run command using the
`--proto` option.

We use the `optimizer` project for our tests.

    >>> project = Project(sample("projects", "optimizers"))

Some helper function:

    >>> def run(*args, **kw):
    ...     runs0 = project.list_runs()
    ...     with Env({"NO_VCS_COMMIT": "1"}):
    ...         project.run(*args, **kw)
    ...     runs1 = project.list_runs()
    ...     # Return the first generated run from command (will
    ...     # be batch when running a batch).
    ...     new_runs = len(runs1) - len(runs0)
    ...     if new_runs == 0:
    ...         return None
    ...     return get_run(new_runs)

    >>> def get_run(index):
    ...     return project.list_runs()[index-1]

    >>> def print_runs():
    ...     project.print_runs(flags=True, status=True)

Start with a single run of `echo` using the default flag values:

    >>> run_1 = run("echo")
    1.0 2 'a'

    >>> print_runs()
    echo  x=1.0 y=2 z=a  completed

Start a second run using our first run as a prototype:

    >>> run_2 = run(proto=run_1.id)
    1.0 2 'a'

We have two distinct runs, each with the same flags.

    >>> print_runs()
    echo  x=1.0 y=2 z=a  completed
    echo  x=1.0 y=2 z=a  completed

## Compare Files

Let's compare the files generated for the two runs.

    >>> run_files = set()
    >>> run_files.update(findl(run_1.dir))
    >>> run_files.update(findl(run_2.dir))

    >>> import filecmp
    >>> same, different, errors = filecmp.cmpfiles(
    ...     run_1.dir, run_2.dir, run_files)

Files that are the same:

    >>> pprint(sorted(same))  # doctest: +REPORT_UDIFF
    ['.guild/attrs/cmd',
     '.guild/attrs/deps',
     '.guild/attrs/exit_status',
     '.guild/attrs/flags',
     '.guild/attrs/host',
     '.guild/attrs/label',
     '.guild/attrs/op',
     '.guild/attrs/platform',
     '.guild/attrs/random_seed',
     '.guild/attrs/sourcecode_digest',
     '.guild/attrs/user',
     '.guild/attrs/user_flags',
     '.guild/opref',
     '.guild/output',
     '.guild/sourcecode/batch_fail.py',
     '.guild/sourcecode/echo.py',
     '.guild/sourcecode/echo2.py',
     '.guild/sourcecode/fail.py',
     '.guild/sourcecode/guild.yml',
     '.guild/sourcecode/noisy.py',
     '.guild/sourcecode/noisy_flubber.py',
     '.guild/sourcecode/poly.py',
     '.guild/sourcecode/trial_fail.py',
     '.guild/sourcecode/tune-echo']

Files that are different:

    >>> sorted(different)
    ['.guild/attrs/env',
     '.guild/attrs/id',
     '.guild/attrs/initialized',
     '.guild/attrs/run_params',
     '.guild/attrs/started',
     '.guild/attrs/stopped',
     '.guild/output.index']

Files that couldn't be compare because they exist in one run but not the other:

    >>> errors
    ['.guild/events.out.tfevents...',
     '.guild/events.out.tfevents...']

## Modify flags

We can modify flags when using a prototype.

    >>> _ = run(proto=run_1.id, flags={"x": 2.0, "z": "b"})
    2.0 2 'b'

    >>> print_runs()
    echo  x=2.0 y=2 z=b  completed
    echo  x=1.0 y=2 z=a  completed
    echo  x=1.0 y=2 z=a  completed

## Modify operation

We can also specify an alternative operation.

    >>> _ = run("echo.py", proto=run_1.id, flags={"x": 3.0, "z": "c"})
    3.0 2 'c'

    >>> print_runs()
    echo.py  x=3.0 y=2 z=c  completed
    echo     x=2.0 y=2 z=b  completed
    echo     x=1.0 y=2 z=a  completed
    echo     x=1.0 y=2 z=a  completed

## Prototypes and Source Code

By default, the source code used for the prototype is used for the new
run.

To illustate, we create a custom project with a sample hello script.

    >>> project = Project(mkdtemp())

    >>> write(path(project.cwd, "hello.py"), """
    ... print('hello-1')
    ... """)

And run the script:

    >>> run_1 = run("hello.py")
    hello-1

Here's the source code copied for the first run:

    >>> cat(path(run_1.dir, ".guild/sourcecode/hello.py"))
    <BLANKLINE>
    print('hello-1')

Let's modify the script to print a different message.

    >>> write(path(project.cwd, "hello.py"), """
    ... print('hello-2')
    ... """)

And confirm the message by running the script a second time (without
using a prototype):

    >>> run_2 = run("hello.py")
    hello-2

The copied source code for the second run:

    >>> cat(path(run_2.dir, ".guild/sourcecode/hello.py"))
    <BLANKLINE>
    print('hello-2')

Let's compare the source code digest for runs 1 and 2 -- they should
be different.

    >>> filecmp.cmpfiles(
    ...     run_1.dir, run_2.dir, [".guild/attrs/sourcecode_digest"])
    ([], ['.guild/attrs/sourcecode_digest'], [])

When we generate a new run with the original run as prototype, we see
the original message.

    >>> run_3 = run(proto=run_1.id)
    hello-1

The source code for run 3:

    >>> cat(path(run_3.dir, ".guild/sourcecode/hello.py"))
    <BLANKLINE>
    print('hello-1')

The source code digest for runs 1 and 3 should be the same.

    >>> filecmp.cmpfiles(
    ...     run_1.dir, run_3.dir, [".guild/attrs/sourcecode_digest"])
    (['.guild/attrs/sourcecode_digest'], [], [])

We can tell Guild to use the working source code rather than the
prototype source code by specifying `force_sourcecode`:

    >>> run_4 = run(proto=run_1.id, force_sourcecode=True)
    hello-2

Here's the source code for latest run:

    >>> cat(path(run_4.dir, ".guild/sourcecode/hello.py"))
    <BLANKLINE>
    print('hello-2')

The source code digest for runs 2 and 4 should be the same.

    >>> filecmp.cmpfiles(
    ...     run_2.dir, run_4.dir, [".guild/attrs/sourcecode_digest"])
    (['.guild/attrs/sourcecode_digest'], [], [])

## Batch Prototypes

Batch prototypes work the same way as normal runs.

Let's run a batch for `echo` in the `optimizers` project.

    >>> project = Project(sample("projects", "optimizers"))

    >>> batch_1 = run("echo", flags={"x": [1,2]})
    INFO: [guild] Running trial ...: echo (x=1.0, y=2, z=a)
    1.0 2 'a'
    INFO: [guild] Running trial ...: echo (x=2.0, y=2, z=a)
    2.0 2 'a'

    >>> print_runs()
    echo   x=2.0 y=2 z=a  completed
    echo   x=1.0 y=2 z=a  completed
    echo+                 completed

Run the operation again using the batch as a prototype:

    >>> batch_2 = run(proto=batch_1.id)
    INFO: [guild] Running trial ...: echo (x=1.0, y=2, z=a)
    1.0 2 'a'
    INFO: [guild] Running trial ...: echo (x=2.0, y=2, z=a)
    2.0 2 'a'

    >>> print_runs()
    echo   x=2.0 y=2 z=a  completed
    echo   x=1.0 y=2 z=a  completed
    echo+                 completed
    echo   x=2.0 y=2 z=a  completed
    echo   x=1.0 y=2 z=a  completed
    echo+                 completed

As with non-batch operations, we can change flags.

    >>> batch_2 = run(proto=batch_1.id, flags={"x": [0.3, 0.4], "y": 3})
    INFO: [guild] Running trial ...: echo (x=0.3, y=3, z=a)
    0.3 3 'a'
    INFO: [guild] Running ...: echo (x=0.4, y=3, z=a)
    0.4 3 'a'

    >>> print_runs()
    echo   x=0.4 y=3 z=a  completed
    echo   x=0.3 y=3 z=a  completed
    echo+                 completed
    echo   x=2.0 y=2 z=a  completed
    echo   x=1.0 y=2 z=a  completed
    echo+                 completed
    echo   x=2.0 y=2 z=a  completed
    echo   x=1.0 y=2 z=a  completed
    echo+                 completed

Let's run these tests with an optimizer.

First delete the runs.

    >>> project.delete_runs()
    Deleted ... run(s)

Run an optimizer batch.

    >>> batch_1 = run("echo", optimizer="gp", max_trials=2,
    ...     flags={"x": "[-1.0:1.0]", "z": "c"},
    ...     opt_flags={"random-starts": 1})
    INFO: [guild] Random start for optimization (1 of 1)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=c)
    ... 2 'c'
    INFO: [guild] Found 1 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=c)
    ... 2 'c'

    >>> print_runs()
    echo     x=... y=2 z=c                                                   completed
    echo     x=... y=2 z=c                                                   completed
    echo+gp  acq-func=gp_hedge kappa=1.96 noise=0.1 random-starts=1 xi=0.05  completed

Start a new batch using the first batch as a prototype and use new
flags for both the user op and the batch:

    >>> batch_2 = run(proto=batch_1.id, flags={"y": 3}, opt_flags={"kappa": 1.5})
    INFO: [guild] Random start for optimization (1 of 1)
    INFO: [guild] Running trial ...: echo (x=..., y=3, z=c)
    ... 3 'c'
    INFO: [guild] Found 1 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: echo (x=..., y=3, z=c)
    ... 3 'c'

    >>> print_runs()
    echo     x=... y=3 z=c                                                   completed
    echo     x=... y=3 z=c                                                   completed
    echo+gp  acq-func=gp_hedge kappa=1.5 noise=0.1 random-starts=1 xi=0.05   completed
    echo     x=... y=2 z=c                                                   completed
    echo     x=... y=2 z=c                                                   completed
    echo+gp  acq-func=gp_hedge kappa=1.96 noise=0.1 random-starts=1 xi=0.05  completed
