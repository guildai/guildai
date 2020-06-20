# Batch runs - basics

These tests illustrate batch run behavior. We'll use the `batch`
sample project:

    >>> project = Project(sample("projects", "batch"))

## Batch runs

A batch run is a run that contains either explicit or implicit batch
specifiers.

Batch runs generate one or more trial runs.

There are two types of implicit batch specifiers:

- Flag list value
- A batch file

A flag list value indicates that the operation should be run for each
value in the list. If there is more tha one flag with list values, the
operation is run over the cartesian product of all flag combinations.

A batch file may contain one or more flag combinations, each of which
is used to run the operation.

If both flag list values and batch files are used, the flag values are
applied to each flag combination in the batch files.

An explicit batch specifier is made using the `--optimizer` flag,
which indicates that the specified optimizer should be used to run the
operation multiple times with the goal of minimizing or maximizing an
operation result.

We'll look at each of these scanarios in the tests below.

## Baseline

For our tests, we'll use a script that prints a message, optionally
capitalizing it.

Here are three runs:

    >>> project.run("say.py", label="default")
    hello

    >>> project.run("say.py", flags={"msg": "hi"}, label="${msg}")
    hi

    >>> project.run("say.py", flags={"msg": "hi", "loud": True},
    ...             label="msg=hi loud=yes")
    HI

    >>> project.print_runs(labels=True)
    say.py  msg=hi loud=yes
    say.py  hi
    say.py  default

Let's delete them in preparation for the next set of tests.

    >>> project.delete_runs()
    Deleted 3 run(s)

## Flag list values

A batch is run impicitly whenever a list of values is specified for a
flag.

Let's run `say.py` with a list of one `msg` flag value:

    >>> project.run("say.py", flags={"msg": ["hi"]})
    INFO: [guild] Running trial ...: say.py (loud=no, msg=hi)
    hi

Here are the trial runs:

    >>> project.print_runs(flags=True)
    say.py   loud=no msg=hi
    say.py+

Note there are two runs. The first run, listed as `+`, is the batch
operation, which is separate from the trial run. The batch operation
uses the special name `+`.

Let's run `say-with-label` for two runs:

    >>> project.run("say-with-label", flags={"msg": ["hi 1", "hi 2"]})
    INFO: [guild] Running trial ...: say-with-label (loud=no, msg='hi 1')
    hi 1
    INFO: [guild] Running trial ...: say-with-label (loud=no, msg='hi 2')
    hi 2

    >>> project.print_runs(labels=True, limit=3)
    say-with-label   msg is 'hi 2'
    say-with-label   msg is 'hi 1'
    say-with-label+

We can preview the trials that will be generated using the
`print_trials` flag:

    >>> project.run("say.py", flags={"msg": ["hi"]}, print_trials=True)
    #  loud  msg
    1  no    hi

Trials are run in order based on flag values.

    >>> project.run("say.py", flags={"msg": ["c", "a", "b"]})
    INFO: [guild] Running trial ...: say.py (loud=no, msg=c)
    c
    INFO: [guild] Running trial ...: say.py (loud=no, msg=a)
    a
    INFO: [guild] Running trial ...: say.py (loud=no, msg=b)
    b

We can specify other flag values:

    >>> project.run("say.py", flags={"msg": ["a", "b"], "loud": True})
    INFO: [guild] Running trial ...: say.py (loud=yes, msg=a)
    A
    INFO: [guild] Running trial ...: say.py (loud=yes, msg=b)
    B

If we use multiple list values, trials are generated using the
cartesian product of all flag combinations. The order of trials
corresponds to the flag names in ascending order followed by the flag
values as ordered in each flag value list.

    >>> project.run("say.py", flags={"msg": ["b", "a"], "loud": [False, True]})
    INFO: [guild] Running trial ...: say.py (loud=no, msg=b)
    b
    INFO: [guild] Running trial ...: say.py (loud=no, msg=a)
    a
    INFO: [guild] Running trial ...: say.py (loud=yes, msg=b)
    B
    INFO: [guild] Running trial ...: say.py (loud=yes, msg=a)
    A

    >>> project.run("say.py", flags={"msg": ["b", "a"], "loud": [False, True]},
    ...              print_trials=True)
    #  loud  msg
    1  no    b
    2  no    a
    3  yes   b
    4  yes   a

## Batch files

Batch files are used to explicitly run batches. A batch file contains
one or more flag combinations that are each used to generate a trial
run.

Guild supports three batch file formats:

- YAML
- JSON
- CSV

Let's look at `batch.csv`, which we can use to run a batch:

    >>> cat(join_path(project.cwd, "batch.csv"))
    msg,loud
    hello 1
    hello 2,yes
    hello 3

CSV files must have a header row that defines the flag names separated
by commas. Each subsequent row is a list of flag values, each
corresponding to a flag name and also separate by commas.

In this case we have a batch of three flag combinations.

Let's delete existing runs in preparation for the tests below.

    >>> project.delete_runs()
    Deleted ... run(s)

Let's use the batch file in an operation:

    >>> project.run("say.py", batch_files=["batch.csv"])
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 1')
    hello 1
    INFO: [guild] Running trial ...: say.py (loud=yes, msg='hello 2')
    HELLO 2
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 3')
    hello 3

    >>> project.run("say.py", batch_files=["batch.csv"], print_trials=True)
    #  loud  msg
    1  no    hello 1
    2  yes   hello 2
    3  no    hello 3

Here's what our runs look like after the batch operation:

    >>> project.print_runs(flags=True)
    say.py   loud=no msg='hello 3'
    say.py   loud=yes msg='hello 2'
    say.py   loud=no msg='hello 1'
    say.py+

In cases where we explicitly define flag values, those flag values are
always used, even if they're defined in batch files.


    >>> project.run("say.py", batch_files=["batch.csv"], flags={"loud": False})
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 1')
    hello 1
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 2')
    hello 2
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 3')
    hello 3

    >>> project.run("say.py", batch_files=["batch.csv"], flags={"loud": False},
    ...             print_trials=True)
    #  loud  msg
    1  no   hello 1
    2  no   hello 2
    3  no   hello 3

We can additionally specify multiple flag values that are used to
generate additional trials.

Here we'll use a list of `loud`, which is applied in cases where
`loud` is not defined in the batch:

    >>> project.run("say.py", batch_files=["batch.csv"],
    ...             flags={"loud": [True, False]})
    INFO: [guild] Running trial ...: say.py (loud=yes, msg='hello 1')
    HELLO 1
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 1')
    hello 1
    INFO: [guild] Running trial ...: say.py (loud=yes, msg='hello 2')
    HELLO 2
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 2')
    hello 2
    INFO: [guild] Running trial ...: say.py (loud=yes, msg='hello 3')
    HELLO 3
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 3')
    hello 3

    >>> project.run("say.py", batch_files=["batch.csv"],
    ...             flags={"loud": [True, False]},
    ...     print_trials=True)
    #  loud  msg
    1  yes   hello 1
    2  no    hello 1
    3  yes   hello 2
    4  no    hello 2
    5  yes   hello 3
    6  no    hello 3

In this case, we drive additional tests by providing a list value for
`msg`.

    >>> project.run("say.py", batch_files=["batch.csv"],
    ...             flags={"msg": ["hello 4", "hello 5"]},
    ...     print_trials=True)
    #  loud  msg
    1  no    hello 4
    2  no    hello 5
    3  yes   hello 4
    4  yes   hello 5
    5  no    hello 4
    6  no    hello 5

Here's `batch.yaml`:

    >>> cat(join_path(project.cwd, "batch.yaml"))
    - msg: hello 4
    - msg: hello 5
    - msg: hello 6
      loud: yes

And the corresponding run:

    >>> project.run("say.py", batch_files=["batch.yaml"])
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 4')
    hello 4
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 5')
    hello 5
    INFO: [guild] Running trial ...: say.py (loud=yes, msg='hello 6')
    HELLO 6

    >>> project.run("say.py", batch_files=["batch.yaml"], print_trials=True)
    #  loud  msg
    1  no    hello 4
    2  no    hello 5
    3  yes   hello 6

And `batch.yml` (different extension):

    >>> cat(join_path(project.cwd, "batch.yml"))
    - msg: hello 77
    - msg: hello 88
      loud: yes
    - msg: hello 99
      loud: no

And the run:

    >>> project.run("say.py", batch_files=["batch.yml"])
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 77')
    hello 77
    INFO: [guild] Running trial ...: say.py (loud=yes, msg='hello 88')
    HELLO 88
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 99')
    hello 99

Here's `batch.json`:

    >>> cat(join_path(project.cwd, "batch.json"))
    [
      {"msg": "hello 7", "loud": false},
      {"msg": "hello 8", "loud": true},
      {"msg": "hello 9", "loud": true}
    ]

And run:

    >>> project.run("say.py", batch_files=["batch.json"])
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 7')
    hello 7
    INFO: [guild] Running trial ...: say.py (loud=yes, msg='hello 8')
    HELLO 8
    INFO: [guild] Running trial ...: say.py (loud=yes, msg='hello 9')
    HELLO 9

    >>> project.run("say.py", batch_files=["batch.json"], print_trials=True)
    #  loud  msg
    1  no    hello 7
    2  yes   hello 8
    3  yes   hello 9

Here's the two batch files used together:

    >>> project.run("say.py", batch_files=["batch.csv", "batch.yaml", "batch.json"])
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 1')
    hello 1
    INFO: [guild] Running trial ...: say.py (loud=yes, msg='hello 2')
    HELLO 2
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 3')
    hello 3
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 4')
    hello 4
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 5')
    hello 5
    INFO: [guild] Running trial ...: say.py (loud=yes, msg='hello 6')
    HELLO 6
    INFO: [guild] Running trial ...: say.py (loud=no, msg='hello 7')
    hello 7
    INFO: [guild] Running trial ...: say.py (loud=yes, msg='hello 8')
    HELLO 8
    INFO: [guild] Running trial ...: say.py (loud=yes, msg='hello 9')
    HELLO 9

    >>> project.run("say.py", batch_files=["batch.csv", "batch.yaml", "batch.json"],
    ...     print_trials=True)
    #  loud  msg
    1  no    hello 1
    2  yes   hello 2
    3  no    hello 3
    4  no    hello 4
    5  no    hello 5
    6  yes   hello 6
    7  no    hello 7
    8  yes   hello 8
    9  yes   hello 9

### Single Batch Runs

When a batch file contains a single run, the flags for that run are
used to generate a single run and not a batch.

    >>> project.run("say.py", batch_files=["single-run.json"])
    hello 10

A batch file may alternatively contain a dict, rather than a list. In
this case the dict is coerced to a list of one item run as a single
run rather than a batch.

    >>> project.run("say.py", batch_files=["single-run-2.json"])
    HELLO 11

And the same for CSV formats:

    >>> project.run("say.py", batch_files=["single-run.csv"])
    HELLO 3.1

### Errors

Unsupported extension:

    >>> project.run("say.py", batch_files=["batch.unknown"])
    guild: cannot read trials for ./batch.unknown: unsupported extension
    <exit 1>

Doesn't exist:

    >>> project.run("say.py", batch_files=["doesnt-exist"])
    guild: batch file ./doesnt-exist does not exist
    <exit 1>

Invalid content:

    >>> project.run("say.py", batch_files=["invalid-data.json"])
    guild: cannot read trials for ./invalid-data.json: invalid data
    type for trials: expected list or dict, got int
    <exit 1>

    >>> project.run("say.py", batch_files=["invalid-item.json"])
    guild: cannot read trials for ./invalid-item.json: invalid data
    type for trial 123: expected dict
    <exit 1>

    >>> project.run("say.py", batch_files=["invalid-item.yaml"])
    guild: cannot read trials for ./invalid-item.yaml: invalid data
    type for trial [1, 2, 3]: expected dict
    <exit 1>

## Saving trials

Batch trials can be saved to a CSV file via the `run` command using
the `save_trials` option.

Here's a directory to save trials in:

    >>> save_dir = mkdtemp()

And path for the saved trials:

    >>> dest_path = path(save_dir, "trials.csv")

Let's run with a set of flags and the `save_trials` flag.

    >>> project.run(
    ...     "add.py",
    ...     flags={"x": [1, 2], "y": [3, 4], "z": [5]},
    ...     save_trials=dest_path)
    Saving trials to .../trials.csv

The contents of our save directory:

    >>> find(save_dir)
    trials.csv

And the trials file:

    >>> cat(dest_path)
    x,y,z
    1,3,5
    1,4,5
    2,3,5
    2,4,5

We can use the trials file to run a batch.

    >>> project.run("add.py", batch_files=[dest_path])
    INFO: [guild] Running trial ...: add.py (x=1, y=3, z=5)
    9
    INFO: [guild] Running trial ...: add.py (x=1, y=4, z=5)
    10
    INFO: [guild] Running trial ...: add.py (x=2, y=3, z=5)
    10
    INFO: [guild] Running trial ...: add.py (x=2, y=4, z=5)
    11
