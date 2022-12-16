# Run With Proto

Runs can be started using settings from other runs. These other runs
are called prototypes and are specified for the run command using the
`--proto` option.

We use the `optimizer` project for our tests.

    >>> use_project("optimizers")

Start with a single run of `echo` using the default flag values.

    >>> run("guild run echo -y")
    1.0 2 'a'

    >>> run("guild runs -s")
    [1]  echo  completed  x=1.00 y=2 z=a

Start a second run using our first run as a prototype.

    >>> echo_1 = run_capture("guild select")

    >>> run(f"guild run --proto {echo_1} -y")
    1.0 2 'a'

    >> run_2 = run(proto=run_1.id)
    1.0 2 'a'

We have two distinct runs, each with the same flags.

    >>> run("guild runs -s")
    [1]  echo  completed  x=1.00 y=2 z=a
    [2]  echo  completed  x=1.00 y=2 z=a

Compare the files generated for the two runs using Python's
`filecmp` module.

    >>> echo_1_dir = run_capture("guild select 1 --path")
    >>> echo_2_dir = run_capture("guild select 2 --path")

    >>> all_files = set()
    >>> all_files.update(findl(echo_1_dir))
    >>> all_files.update(findl(echo_2_dir))

    >>> import filecmp
    >>> same, different, errors = filecmp.cmpfiles(
    ...     echo_1_dir, echo_2_dir, all_files)

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
     '.guild/attrs/plugins',
     '.guild/attrs/random_seed',
     '.guild/attrs/sourcecode_digest',
     '.guild/attrs/user',
     '.guild/attrs/user_flags',
     '.guild/manifest',
     '.guild/opref',
     '.guild/output',
     'batch_fail.py',
     'dummy.qmd',
     'dummy.r',
     'echo.py',
     'echo2.py',
     'fail.py',
     'guild.yml',
     'noisy.py',
     'noisy_flubber.py',
     'poly.py',
     'trial_fail.py']

Files that are different:

    >>> pprint(sorted(different))  # doctest: +REPORT_UDIFF
    ['.guild/attrs/env',
     '.guild/attrs/id',
     '.guild/attrs/initialized',
     '.guild/attrs/run_params',
     '.guild/attrs/started',
     '.guild/attrs/stopped',
     '.guild/output.index']

Files that couldn't be compare because they exist in one run but not
the other:

    >>> pprint(sorted(errors))  # doctest: +REPORT_UDIFF
    ['.guild/events.out.tfevents...',
     '.guild/events.out.tfevents...']

### Source code

The source code from the proto is copied to the new run. The
sourcecode listings for the two runs should be identical.

    >>> echo_1_sourcecode = run_capture("guild ls --sourcecode 1 -n")
    >>> echo_2_sourcecode = run_capture("guild ls --sourcecode 2 -n")

    >>> echo_1_sourcecode == echo_2_sourcecode, (echo_1_sourcecode, echo_2_sourcecode)
    (True, ...)

### Source code manifests

When initializing the new run, Guild re-generates the manifest for the
actual copied files.

Because the source code for the original run (the prototype) did not
change, the manfiest files should be identical.

    >>> diff(path(echo_1_dir, ".guild", "manifest"),
    ...      path(echo_2_dir, ".guild", "manifest"))

## Modify flags

We can modify flags when using a prototype.

    >>> run(f"guild run --proto {echo_1} x=2 z=b -y")
    2.0 2 'b'

    >>> run("guild runs -s")
    [1]  echo  completed  x=2.00 y=2 z=b
    [2]  echo  completed  x=1.00 y=2 z=a
    [3]  echo  completed  x=1.00 y=2 z=a

    >>> run("guild select --attr flags")
    x: 2.0
    y: 2
    z: b

## Modify operation

We can specify an alternative operation.

    >>> run(f"guild run echo.py --proto {echo_1} x=3.0 y=4 z=c -y")
    3.0 4 'c'

    >>> run("guild runs -s")
    [1]  echo.py  completed  x=3.00 y=4 z=c
    [2]  echo     completed  x=2.00 y=2 z=b
    [3]  echo     completed  x=1.00 y=2 z=a
    [4]  echo     completed  x=1.00 y=2 z=a

## Prototypes and Source Code

By default, the source code used for the prototype is used for the new
run. Guild alternatively supports using the current project source
code.

To illustrate, create a new project.

    >>> hello_project = mkdtemp()
    >>> use_project(hello_project)

Create a simple script that prints a message.

    >>> write("hello.py", "print('hello-1')")

Run the script. We use a label to identify the run later.

    >>> run("guild run hello.py --label hello-1 -y")
    hello-1

Modify the script, simulating a user's ongoing work.

    >>> write("hello.py", "print('hello-2')")

When we run the script, we get a different message, as expected.

    >>> run("guild run hello.py --label hello-2 -y")
    hello-2

Start a new run, using the first hello run as a prototype.

    >>> run("guild runs -s")
    [1]  hello.py  completed  hello-2
    [2]  hello.py  completed  hello-1

    >>> hello_1 = run_capture("guild select -Fl hello-1")

    >>> run(f"guild run --proto {hello_1} --label hello-1-2 -y")
    hello-1

Note the run prints the message from the original source code.

Next, create a new run using the original run as prototype but with
the project source code (using the `--force-sourcecode` option).

    >>> run(f"guild run --proto {hello_1} --label hello-1-3 --force-sourcecode -y")
    hello-2

Let's look at the results for the four runs.

    >>> run("guild runs -s")
    [1]  hello.py  completed  hello-1-3
    [2]  hello.py  completed  hello-1-2
    [3]  hello.py  completed  hello-2
    [4]  hello.py  completed  hello-1

First run (source code baseline):

    >>> run("guild cat -p hello.py 4")
    print('hello-1')

    >>> run("guild cat --output 4")
    hello-1

    >>> run("guild select --attr sourcecode_digest 4")
    a17a8625d62d51b51264a0a4757fefa8

Second run (reflects modified source code):

    >>> run("guild cat -p hello.py 3")
    print('hello-2')

    >>> run("guild cat --output 3")
    hello-2

    >>> run("guild select --attr sourcecode_digest 3")
    e0c8c7babaeb011426609e980529e4d5

Third run (prototype using run source code):

    >>> run("guild cat -p hello.py 2")
    print('hello-1')

    >>> run("guild cat --output 2")
    hello-1

    >>> run("guild select --attr sourcecode_digest 2")
    a17a8625d62d51b51264a0a4757fefa8

Fourth run (prototype uses project source code):

    >>> run("guild cat -p hello.py 1")
    print('hello-2')

    >>> run("guild cat --output 1")
    hello-2

    >>> run("guild select --attr sourcecode_digest 1")
    e0c8c7babaeb011426609e980529e4d5

## Batch prototypes

Batch prototypes work the same way as normal runs.

Switch back to the `optimizers` project.

    >>> use_project("optimizers")

Run a batch of two runs for `echo`. We use `--keep-batch` to ensure
that Guild does not delete the batch run, which it does by default.

    >>> run("guild run echo x=[1,2] --keep-batch -y")
    INFO: [guild] Running trial ...: echo (x=1.0, y=2, z=a)
    1.0 2 'a'
    INFO: [guild] Running trial ...: echo (x=2.0, y=2, z=a)
    2.0 2 'a'

    >>> run("guild runs -s")
    [1]  echo   completed  x=2.00 y=2 z=a
    [2]  echo   completed  x=1.00 y=2 z=a
    [3]  echo+  completed

Run the operation again using the batch as a prototype.

    >>> batch_1 = run_capture("guild select 3")

    >>> run(f"guild run --proto {batch_1} --keep-batch -y")
    INFO: [guild] Running trial ...: echo (x=1.0, y=2, z=a)
    1.0 2 'a'
    INFO: [guild] Running trial ...: echo (x=2.0, y=2, z=a)
    2.0 2 'a'

    >>> run("guild runs -s")
    [1]  echo   completed  x=2.00 y=2 z=a
    [2]  echo   completed  x=1.00 y=2 z=a
    [3]  echo+  completed
    [4]  echo   completed  x=2.00 y=2 z=a
    [5]  echo   completed  x=1.00 y=2 z=a
    [6]  echo+  completed

As with non-batch operations, we can change flags.

    >>> run(f"guild run --proto {batch_1} --keep-batch y=[3,4] -y")
    INFO: [guild] Running trial ...: echo (x=1.0, y=3, z=a)
    1.0 3 'a'
    INFO: [guild] Running trial ...: echo (x=1.0, y=4, z=a)
    1.0 4 'a'
    INFO: [guild] Running trial ...: echo (x=2.0, y=3, z=a)
    2.0 3 'a'
    INFO: [guild] Running trial ...: echo (x=2.0, y=4, z=a)
    2.0 4 'a'

    >>> run("guild runs -s")
    [1]   echo   completed  x=2.00 y=4 z=a
    [2]   echo   completed  x=2.00 y=3 z=a
    [3]   echo   completed  x=1.00 y=4 z=a
    [4]   echo   completed  x=1.00 y=3 z=a
    [5]   echo+  completed
    [6]   echo   completed  x=2.00 y=2 z=a
    [7]   echo   completed  x=1.00 y=2 z=a
    [8]   echo+  completed
    [9]   echo   completed  x=2.00 y=2 z=a
    [10]  echo   completed  x=1.00 y=2 z=a
    [11]  echo+  completed

## Optimizer prototypes

We can use optimizer runs as prototypes as well.

Reset our environment.

    >>> use_project("optimizers")

Run an optimizer batch.

    >>> run("guild run echo -o gp --trials 2 "
    ...     "x=[-1.0:1.0] z=c -Fo random-starts=1 -y")
    INFO: [guild] Random start for optimization (1 of 1)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=c)
    ... 2 'c'
    INFO: [guild] Found 1 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=c)
    ... 2 'c'

    >>> run("guild runs -s")
    [1]  echo           completed  x=... y=2 z=c
    [2]  echo           completed  x=... y=2 z=c
    [3]  echo+skopt:gp  completed  acq-func=gp_hedge kappa=1.96 noise=0.1 prev-trials=batch random-starts=1 xi=0.05

Start a new optimization run using the first optimization run as a
prototype.

    >>> opt_1 = run_capture("guild select 3")

    >>> run(f"guild run --proto {opt_1} -y")
    INFO: [guild] Random start for optimization (1 of 1)
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=c)
    ... 2 'c'
    INFO: [guild] Found 1 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: echo (x=..., y=2, z=c)
    ... 2 'c'

    >>> run("guild runs -s")
    [1]   echo           completed  x=... y=2 z=c
    [2]   echo           completed  x=... y=2 z=c
    [3]   echo+skopt:gp  completed  acq-func=gp_hedge kappa=1.96 noise=0.1 prev-trials=batch random-starts=1 xi=0.05
    [4]   echo           completed  x=... y=2 z=c
    [5]   echo           completed  x=... y=2 z=c
    [6]   echo+skopt:gp  completed  acq-func=gp_hedge kappa=1.96 noise=0.1 prev-trials=batch random-starts=1 xi=0.05

Generate another optimization run using the second optimizer run but
with different flag values and an additional trial.

    >>> opt_2 = run_capture("guild select 3")

    >>> run(
    ...     f"guild run --proto {opt_2} y=3 "
    ...     "-Fo kappa=1.5 -Fo random-starts=2 "
    ...     "--trials 3 -y")
    INFO: [guild] Random start for optimization (1 of 2)
    INFO: [guild] Running trial ...: echo (x=..., y=3, z=c)
    ... 3 'c'
    INFO: [guild] Random start for optimization (2 of 2)
    INFO: [guild] Running trial ...: echo (x=..., y=3, z=c)
    ... 3 'c'
    INFO: [guild] Found 2 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: echo (x=..., y=3, z=c)
    ... 3 'c'

    >>> run("guild runs -s")
    [1]   echo           completed  x=... y=3 z=c
    [2]   echo           completed  x=... y=3 z=c
    [3]   echo           completed  x=... y=3 z=c
    [4]   echo+skopt:gp  completed  acq-func=gp_hedge kappa=1.5 noise=0.1 prev-trials=batch random-starts=2 xi=0.05
    [5]   echo           completed  x=... y=2 z=c
    [6]   echo           completed  x=... y=2 z=c
    [7]   echo+skopt:gp  completed  acq-func=gp_hedge kappa=1.96 noise=0.1 prev-trials=batch random-starts=1 xi=0.05
    [8]   echo           completed  x=... y=2 z=c
    [9]   echo           completed  x=... y=2 z=c
    [10]  echo+skopt:gp  completed  acq-func=gp_hedge kappa=1.96 noise=0.1 prev-trials=batch random-starts=1 xi=0.05
