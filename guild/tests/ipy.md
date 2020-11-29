# Interactive Python interface

The `ipy` module provides an interactive interface to Guild operations
that is Notebook friendly.

    >>> from guild import ipy
    >>> from guild import config

Create a Guild home for our tests:

    >>> guild_home = config.SetGuildHome(mkdtemp())

Define a simple function to run:

    >>> def hello(msg, n=3):
    ...     touch("marker")
    ...     for i in range(n):
    ...         print("%s %i!" % (msg, i + 1))

For displaying Pandas dataframes, which are used by `ipy` for tabular
data, we want to control the formatting for consistency across tests.

    >>> import pandas as pd
    >>> pd.set_option("display.expand_frame_repr", False)

## Running an operation

The `ipy` interface runs operations as Python functions. Flags are
provided as key words:

    >>> with guild_home:
    ...     run, result = ipy.run(hello, msg="Hello")
    Hello 1!
    Hello 2!
    Hello 3!

    >>> run
    <guild.run.Run '...'>

    >>> print(result)
    None

Files:

    >>> find(run.path)
    .guild/attrs/exit_status
    .guild/attrs/flags
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/label
    .guild/attrs/started
    .guild/attrs/stopped
    .guild/opref
    .guild/output
    marker

Output:

    >>> cat(run.guild_path("output"))
    Hello 1!
    Hello 2!
    Hello 3!

Run another operation:

    >>> with guild_home:
    ...     run2, _ = ipy.run(hello, msg="Hola", n=2, _label="run2")
    Hola 1!
    Hola 2!

run2 occurs after run:

    >>> run2.timestamp > run.timestamp, run2.timestamp, run.timestamp
    (True, ...)

Another operation using tag for label:

    >>> with guild_home:
    ...     run3, _ = ipy.run(hello, msg="Ya", n=1, _tag="run3")
    Ya 1!

## List runs

List runs:

    >>> with guild_home:
    ...     ipy.runs()
       run  operation  started     status            label
    0  ...    hello()      ...  completed  run3 msg=Ya n=1
    1  ...    hello()      ...  completed             run2
    2  ...    hello()      ...  completed    msg=Hello n=3

Filter using a label:

    >>> with guild_home:
    ...     ipy.runs(labels=["run2"])
       run  operation  started     status label
    0  ...    hello()      ...  completed run2

Filter with status:

    >>> with guild_home:
    ...     ipy.runs(error=True, terminated=True)
    Empty RunsDataFrame
    Columns: [run, operation, started, status, label]
    Index: []

With operation:

    >>> with guild_home:
    ...     ipy.runs(operations=["hello"], completed=True)
       run  operation  started     status            label
    0  ...    hello()      ...  completed  run3 msg=Ya n=1
    1  ...    hello()      ...  completed             run2
    2  ...    hello()      ...  completed    msg=Hello n=3

    >>> with guild_home:
    ...     ipy.runs(operations=["bye"])
    Empty RunsDataFrame
    Columns: [run, operation, started, status, label]
    Index: []

## Runs info

Print latest run info:

    >>> with guild_home:
    ...     ipy.runs().info()
    id: ...
    operation: hello()
    status: completed
    started: ...
    stopped: ...
    label: run3 msg=Ya n=1
    run_dir: ...
    flags:
      msg: Ya
      n: 1

Info for a specific run:

    >>> with guild_home:
    ...     ipy.runs().iloc[1].info()
    id: ...
    operation: hello()
    status: completed
    started: ...
    stopped: ...
    label: run2
    run_dir: ...
    flags:
      msg: Hola
      n: 2

Info with output:

    >>> with guild_home:
    ...     ipy.runs().iloc[1].info(output=True)
    id: ...
    ...
    output:
      Hola 1!
      Hola 2!

Info with scalars (no scalars for this run, so list is empty):

    >>> with guild_home:
    ...     ipy.runs().iloc[1].info(scalars=True)
    id: ...
    ...
    scalars:

## Flags

Flags can be read as a data frame using the `flags()` function on runs.

    >>> with guild_home:
    ...     runs = ipy.runs()

    >>> flags = runs.flags()

    >>> flags
         msg  n  run
    0     Ya  1  ...
    1   Hola  2  ...
    2  Hello  3  ...

    >>> pprint(flags.to_dict("records"))
    [{'msg': 'Ya', 'n': 1, 'run': '...'},
     {'msg': 'Hola', 'n': 2, 'run': '...'},
     {'msg': 'Hello', 'n': 3, 'run': '...'}]

## Delete runs

Delete runs:

    >>> with guild_home:
    ...     ipy.runs().delete()
    ['...', '...']

    >>> with guild_home:
    ...     ipy.runs()
    Empty RunsDataFrame
    Columns: [run, operation, started, status, label]
    Index: []

Deleting an empty list:

    >>> with guild_home:
    ...     ipy.runs().delete()
    []

## Logging scalars

The `ipy` interface does not provide an explicit interface for
logging scalars. This follows the convention used in Guild's script
interface, which is to not provide a Guild-specific
interface. Instead, operations use standard conventions.

In the case of flags, values are pass to the function as function key
words.

Scalars represent the output metrics of a function. These might
typically be returned as a dict. However, it's important to let
functions log values as they run. Return values are therefore
insufficient.

Furthermore, we want to support a seamless migration of functions to
scripts.

With these points in mind, `ipy` supports scalar logging in two ways:

- Printing values to stdout
- Logging scalars in TF event files

### Printing scalars to stdout

Here's a function that prints scalar values to stdout:

    >>> def op1(a, b):
    ...     print("x: %i" % (a + b))
    ...     print("y: %i" % (a - b))
    ...     print("z: %i" % (b - a))

Run the operation:

    >>> with guild_home:
    ...     run, _result = ipy.run(op1, a=1, b=2)
    x: 3
    y: -1
    z: 1

Files:

    >>> find(run.path)
    .guild/attrs/exit_status
    .guild/attrs/flags
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/label
    .guild/attrs/started
    .guild/attrs/stopped
    .guild/events.out.tfevents...
    .guild/opref
    .guild/output

Note that output now contains a `tsevents` file.

Read the scalars:

    >>> with guild_home:
    ...     scalars = ipy.runs().scalars()

    >>> scalars
       run  prefix tag  first_val  first_step  last_val  last_step  min_val  min_step  max_val  max_step  avg_val  count  total
    0  ...  .guild   x        3.0           0       3.0          0      3.0         0      3.0         0      3.0      1    3.0
    1  ...  .guild   y       -1.0           0      -1.0          0     -1.0         0     -1.0         0     -1.0      1   -1.0
    2  ...  .guild   z        1.0           0       1.0          0      1.0         0      1.0         0      1.0      1    1.0

Print some of the more interesting columns:

    >>> scalars[["run", "tag", "last_step", "last_val"]]
       run tag  last_step  last_val
    0  ...   x          0       3.0
    1  ...   y          0      -1.0
    2  ...   z          0       1.0

The underlying scalar summaries can be read using `scalars_detail`.

    >>> with guild_home:
    ...     ipy.runs().scalars_detail()
       run    path tag  val  step
    0  ...  .guild   x  3.0     0
    1  ...  .guild   y -1.0     0
    2  ...  .guild   z  1.0     0

### Logging scalars as TFEvents

This function uses Guild's `SummaryWriter` to write scalars.

    >>> from guild.summary import SummaryWriter

    >>> def op2(a, c):
    ...     writer = SummaryWriter(".")
    ...     writer.add_scalar("x", a + c, 1)
    ...     writer.add_scalar("x", a + c + 1, 2)
    ...     writer.add_scalar("x", a + c + 2, 3)
    ...     writer.close()

Let's run the function as an operation:

    >>> with guild_home:
    ...     run, _result = ipy.run(op2, a=1.0, c=0.0)

The run files:

    >>> find(run.path)
    .guild/attrs/exit_status
    .guild/attrs/flags
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/label
    .guild/attrs/started
    .guild/attrs/stopped
    .guild/opref
    .guild/output
    events.out.tfevents...

And its scalars:

    >>> with guild_home:
    ...     runs = ipy.runs()
    >>> scalars = runs.loc[runs["run"] == run.id].scalars()
    >>> pprint(scalars.to_dict("records"))
    [{'avg_val': 2.0,
      'count': 3,
      'first_step': 1,
      'first_val': 1.0,
      'last_step': 3,
      'last_val': 3.0,
      'max_step': 3,
      'max_val': 3.0,
      'min_step': 1,
      'min_val': 1.0,
      'prefix': '',
      'run': '...',
      'tag': 'x',
      'total': 6.0}]

Scalars detail:

    >>> runs.loc[runs["run"] == run.id].scalars_detail()
       run path tag  val  step
    0  ...    .   x  1.0     1
    1  ...    .   x  2.0     2
    2  ...    .   x  3.0     3

## Comparing runs

The `compare()` function can be applied to a list of runs to return a
data frame that has both flags and scalars.

    >>> with guild_home:
    ...     compare = ipy.runs().compare()

    >>> compare
       run operation started  time     status        label    a    b    c  step    x    y    z
    0  ...     op2()     ...   ...  completed  a=1.0 c=0.0  1.0  NaN  0.0     3  3.0  NaN  NaN
    1  ...     op1()     ...   ...  completed      a=1 b=2  1.0  2.0  NaN     0  3.0 -1.0  1.0

    >>> compare.info()  # doctest: -PY3
    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 2 entries, 0 to 1
    Data columns (total 13 columns):
    run          2 non-null object
    operation    2 non-null object
    started      2 non-null datetime64[ns]
    time         2 non-null timedelta64[ns]
    status       2 non-null object
    label        2 non-null object
    a            2 non-null float64
    b            1 non-null float64
    c            1 non-null float64
    step         2 non-null int64
    x            2 non-null float64
    y            1 non-null float64
    z            1 non-null float64
    dtypes: datetime64[ns](1), float64(6), int64(1), object(4), timedelta64[ns](1)
    memory usage: ...

    >>> compare.info()  # doctest: -PY2 -PY35 -PY37
    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 2 entries, 0 to 1
    Data columns (total 13 columns):
     #   Column     Non-Null Count  Dtype
    ---  ------     --------------  -----
     0   run        2 non-null      object
     1   operation  2 non-null      object
     2   started    2 non-null      datetime64[ns]
     3   time       2 non-null      timedelta64[ns]
     4   status     2 non-null      object
     5   label      2 non-null      object
     6   a          2 non-null      float64
     7   b          1 non-null      float64
     8   c          1 non-null      float64
     9   step       2 non-null      int64
     10  x          2 non-null      float64
     11  y          1 non-null      float64
     12  z          1 non-null      float64
    dtypes: datetime64[ns](1), float64(6), int64(1), object(4), timedelta64[ns](1)
    memory usage: ...

## Grid search

The `run` function will generate trials for values provided in list
args.

Let's clear our runs in preparation for our new trials.

    >>> with guild_home:
    ...     len(runs.delete())
    2

Run `op1` with two values for each of the two arguments. This will
generate four trials.

    >>> with guild_home:
    ...     runs, results = ipy.run(op1, a=[1,2], b=[3,4])
    Running op1 (a=1, b=3):
    x: 4
    y: -2
    z: 2
    Running op1 (a=1, b=4):
    x: 5
    y: -3
    z: 3
    Running op1 (a=2, b=3):
    x: 5
    y: -1
    z: 1
    Running op1 (a=2, b=4):
    x: 6
    y: -2
    z: 2

Generated runs:

    >>> runs
    [<guild.run.Run '...'>,
     <guild.run.Run '...'>,
     <guild.run.Run '...'>,
     <guild.run.Run '...'>]

And op return values:

    >>> results
    [None, None, None, None]

## Random search

Random search uses randomly generated flag values when running
trials. A random search can be performed in various ways:

- Explicitly specify "random" as the `_optimizer` run option
- Specify a slice object for one or more flag values when `_optimizer`
  is not specified

Let's run three trials using "random" optimizer. First, clear existing
runs.

    >>> with guild_home:
    ...     len(ipy.runs().delete())
    4

Run three trials selecting random values for `a` over the range `-10`
to `10` and the value `12` for `b`. Use fixed random seed to let us
assert the generated values.

    >>> with guild_home:
    ...     runs, _ = ipy.run(op1, a=slice(0, 5), b=12,
    ...                       _max_trials=3, _random_seed=1)
    Running op1 (a=3, b=12):
    x: 15
    y: -9
    z: 9
    Running op1 (a=4, b=12):
    x: 16
    y: -8
    z: 8
    Running op1 (a=0, b=12):
    x: 12
    y: -12
    z: 12

    >>> len(runs)
    3

    >>> pprint(runs[0].get("flags"))
    {'a': 3, 'b': 12}

    >>> pprint(runs[1].get("flags"))
    {'a': 4, 'b': 12}

    >>> pprint(runs[2].get("flags"))
    {'a': 0, 'b': 12}

If a `_label` arg is not specified, each run has gets a default label.

    >>> [runs[i].get("label") for i in range(3)]
    ['a=3 b=12', 'a=4 b=12', 'a=0 b=12']

We can alternatively use a range function, which indicates the type of
distribution to sample from. We also specify a label.

    >>> with guild_home:
    ...     runs, _ = ipy.run(op1, a=ipy.uniform(0, 5), b=12,
    ...                       _label="random-2",
    ...                       _max_trials=3,
    ...                       _random_seed=1)
    Running op1 (a=3, b=12):
    x: 15
    y: -9
    z: 9
    Running op1 (a=4, b=12):
    x: 16
    y: -8
    z: 8
    Running op1 (a=0, b=12):
    x: 12
    y: -12
    z: 12

The specified label is used for each run:

    >>> [runs[i].get("label") for i in range(3)]
    ['random-2', 'random-2', 'random-2']

Finally, we can specify an explicit "random" optimizer:

    >>> with guild_home:
    ...     runs, _ = ipy.run(op1, a=slice(0, 5), b=12,
    ...                      _optimizer="random",
    ...                      _label="random-3",
    ...                      _max_trials=3,
    ...                      _random_seed=1)
    Running op1 (a=3, b=12):
    x: 15
    y: -9
    z: 9
    Running op1 (a=4, b=12):
    x: 16
    y: -8
    z: 8
    Running op1 (a=0, b=12):
    x: 12
    y: -12
    z: 12

    >>> [runs[i].get("label") for i in range(3)]
    ['random-3', 'random-3', 'random-3']

## Hyperparameter optimization

Guild `ipy` supports other optimizers including "gp", "forest", and
"gbrt".

Let's clear our runs first:

    >>> with guild_home:
    ...     len(ipy.runs().delete())
    9

Run `op1` for three runs using the "gp" optimizer to minimize scalar
`x` where both `a` and `b` are selected from uniform distributions.

This operation logs progress, so we capture logs.

    >>> with guild_home:
    ...     with LogCapture() as logs:
    ...         runs, _ = ipy.run(op1, a=slice(-10,10), b=slice(-5, 5),
    ...                 _optimizer="gp",
    ...                 _minimize="x",
    ...                 _max_trials=3,
    ...                 _random_seed=1,
    ...                 _opt_xi=0.02)
    Running op1 (a=-2, b=2):
    x: 0
    y: -4
    z: 4
    Running op1 (a=10, b=-5):
    x: 5
    y: 15
    z: -15
    Running op1 (a=10, b=5):
    x: 15
    y: 5
    z: -5

    >>> logs.print_all()
    Random start for optimization (missing previous trials)
    Found 1 previous trial(s) for use in optimization
    Found 2 previous trial(s) for use in optimization

    >>> len(runs)
    3

We can see the generated runs in Guild home:

    >>> with guild_home:
    ...     ipy.runs()
       run operation  started     status       label
    0  ...     op1()      ...  completed    a=10 b=5
    1  ...     op1()      ...  completed   a=10 b=-5
    2  ...     op1()      ...  completed    a=-2 b=2

### Other Optimizers

Random forest:

    >>> with guild_home:
    ...     with LogCapture() as logs:
    ...         runs, _ = ipy.run(op1, a=slice(-10,10), b=slice(-5, 5),
    ...                 _optimizer="forest",
    ...                 _minimize="x",
    ...                 _max_trials=3,
    ...                 _random_seed=1,
    ...                 _opt_random_starts=2,
    ...                 _opt_kappa=2.0,
    ...                 _opt_xi=0.05)
    Running op1 (a=1, b=3):
    x: 4
    y: -2
    z: 2
    Running op1 (a=8, b=3):
    x: 11
    y: 5
    z: -5
    Running op1 (a=10, b=-4):
    x: 6
    y: 14
    z: -14

    >>> logs.print_all()
    Random start for optimization (1 of 2)
    Random start for optimization (2 of 2)
    Found 2 previous trial(s) for use in optimization

Gradient boosted regression trees:

    >>> with guild_home:
    ...     with LogCapture() as logs:
    ...         runs, _ = ipy.run(op1, a=slice(-10,10), b=slice(-5, 5),
    ...                 _optimizer="gbrt",
    ...                 _minimize="x",
    ...                 _max_trials=4,
    ...                 _random_seed=2,
    ...                 _opt_random_starts=2,
    ...                 _tag="gbrt",
    ...                 _opt_kappa=2.0)
    Running op1 (a=-2, b=3):
    x: 1
    y: -5
    z: 5
    Running op1 (a=4, b=0):
    x: 4
    y: 4
    z: -4
    Running op1 (a=-4, b=3):
    x: -1
    y: -7
    z: 7
    Running op1 (a=-9, b=-5):
    x: -14
    y: -4
    z: 4

    >>> logs.print_all()
    Random start for optimization (1 of 2)
    Random start for optimization (2 of 2)
    Found 2 previous trial(s) for use in optimization
    Found 3 previous trial(s) for use in optimization

    >>> with guild_home:
    ...     ipy.runs(labels=["gbrt"])
       run  operation  started     status           label
    0  ...      op1() ...  completed  gbrt a=-9 b=-5
    1  ...      op1() ...  completed   gbrt a=-4 b=3
    2  ...      op1() ...  completed    gbrt a=4 b=0
    3  ...      op1() ...  completed   gbrt a=-2 b=3

Unsupported optimizer:

    >>> with guild_home:
    ...     ipy.run(op1, a=1, b=2, _optimizer="not supported")
    Traceback (most recent call last):
    TypeError: optimizer 'not supported' is not supported

## Alternative Operation Implementations

Operations may be bound methods.

    >>> class Trainer:
    ...     def train(self, lr):
    ...         print("Training with lr=%s" % lr)

    >>> with guild_home:
    ...     ipy.run(Trainer().train, 0.1)
    Training with lr=0.1
    (<guild.run.Run '...'>, None)

    >>> with guild_home:
    ...     ipy.runs().info()
    id: ...
    operation: train()
    status: completed
    started: ...
    stopped: ...
    label: lr=0.1
    run_dir: ...
    flags:
      lr: 0.1

Operations may be implemented as Python callables.

    >>> class Op:
    ...     def __call__(self, a, b, c=3):
    ...         return a, b, c

    >>> with guild_home:
    ...     ipy.run(Op(), 1, 2)
    (<guild.run.Run '...'>, (1, 2, 3))

    >>> with guild_home:
    ...     ipy.runs().info()
    id: ...
    operation: Op()
    status: completed
    started: ...
    stopped: ...
    label: a=1 b=2 c=3
    run_dir: ...
    flags:
      a: 1
      b: 2
      c: 3

Operation implemented as static method:

    >>> class Trainer2:
    ...     @staticmethod
    ...     def train(dropout=0.2):
    ...         print("Training with dropout=%s" % dropout)

    >>> with guild_home:
    ...     ipy.run(Trainer2().train)
    Training with dropout=0.2
    (<guild.run.Run '...'>, None)

    >>> with guild_home:
    ...     ipy.runs().info()
    id: ...
    operation: train()
    status: completed
    started: ...
    stopped: ...
    label: dropout=0.2
    run_dir: ...
    flags:
      dropout: 0.2

Implemented as a class method:

    >>> class Trainer3:
    ...     model_name = "ze model"
    ...
    ...     @classmethod
    ...     def train(cls, batch_size):
    ...         print("Train %s with batch_size=%s" % (cls.model_name, batch_size))

    >>> with guild_home:
    ...     ipy.run(Trainer3().train, 200)
    Train ze model with batch_size=200
    (<guild.run.Run '...'>, None)

    >>> with guild_home:
    ...     ipy.runs().info()
    id: ...
    operation: train()
    status: completed
    started: ...
    stopped: ...
    label: batch_size=200
    run_dir: ...
    flags:
      batch_size: 200

## Run Exceptions

If a run operation raises an exception, Guild handles the exception by
logging an error and raises RunError, which contains a reference to
the run and the original exception.

Here's an operation that raises an error:

    >>> def error():
    ...     raise Exception("boom")

When we run the operation, we get a traceback from the original error
with `RunError`.

    >>> with guild_home:
    ...     ipy.run(error)
    Traceback (most recent call last):
      ...
      File "<doctest ipy.md[...]>", line 2, in error
        raise Exception("boom")
    ...
    RunError: (<guild.run.Run '...'>, Exception('boom'...))

Let's run again and catch the error to inspect it.

    >>> with guild_home:
    ...     try:
    ...         ipy.run(error)
    ...     except ipy.RunError as e:
    ...         print(e.run)
    ...         print(repr(e.from_exc))
    <guild.run.Run '...'>
    Exception('boom'...)

Here are the last two runs and their status:

    >>> with guild_home:
    ...     ipy.runs()[:2]
       run operation started status label
    0  ... error()       ...  error
    1  ... error()       ...  error

And the exit status for the last run:

    >>> with guild_home:
    ...     ipy.runs().iloc[0][0].run.get("exit_status")
    1

When KeyboardInterrupt is raised - as it the case when the user types
Ctrl-C during an operation, Guild handles the exception as a SIGTERM
result and raises RunTerminated.

A function that simulated Ctrl-C by the user:

    >>> def ctrl_c():
    ...     raise KeyboardInterrupt()

The exception:

    >>> with guild_home:
    ...     ipy.run(ctrl_c)
    Traceback (most recent call last):
      ...
      File "<doctest ipy.md[73]>", line 2, in ctrl_c
        raise KeyboardInterrupt()
    ...
    RunTerminated: (<guild.run.Run '...'>, KeyboardInterrupt())

The generated run:

    >>> with guild_home:
    ...     ipy.runs()[:1]
       run operation started status     label
    0  ... ctrl_c()      ... terminated

The generated run exit status:

    >>> with guild_home:
    ...     ipy.runs().iloc[0][0].run.get("exit_status")
    -15

## Run Process

Runs started using `ipy` use the Python interpreter pid as process
lock.

Let's start an operation in a separate thread.

    >>> import threading

    >>> class BackgroundOp(threading.Thread):
    ...     def __init__(self, in_q, out_q):
    ...         super(BackgroundOp, self).__init__()
    ...         self.in_q = in_q
    ...         self.out_q = out_q
    ...
    ...     def run(self):
    ...         with guild_home:
    ...             ipy.run(self._op, _op_name="op-in-thread")
    ...
    ...     def _op(self):
    ...         self.out_q.put("started")
    ...         self.in_q.get()

Use a queues to communicate with the thread.

    >>> from six.moves import queue
    >>> in_q = queue.Queue()
    >>> out_q = queue.Queue()

Start the operation in the background as a thread.

    >>> op = BackgroundOp(in_q, out_q)
    >>> op.start()

Wait for the operation to start.

    >>> out_q.get()
    'started'

The run latest run status is 'running':

    >>> with guild_home:
    ...     ipy.runs().info()
    id: ...
    operation: op-in-thread()
    status: running
    started: ...
    stopped:
    label:
    run_dir: ...
    flags:

Notify the op to finish.

    >>> in_q.put("stop")
    >>> op.join(0.1)

And the run status after stopping:

    >>> with guild_home:
    ...     ipy.runs().info()
    id: ...
    operation: op-in-thread()
    status: completed
    started: ...
    stopped: ...
    label:
    run_dir: ...
    flags:

# Relative Guild Home

Run `hello` above using a relative Guild home. This simulates the use
of a relative Guild home used in any examples.

    >>> guild_home_dir = mkdtemp()

    >>> with Chdir(dirname(guild_home_dir)):
    ...     with SetGuildHome(basename(guild_home_dir)):
    ...         run, result = ipy.run(hello, msg="Hello")
    ...     find(run.dir)
    Hello 1!
    Hello 2!
    Hello 3!
    .guild/attrs/exit_status
    .guild/attrs/flags
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/label
    .guild/attrs/started
    .guild/attrs/stopped
    .guild/opref
    .guild/output
    marker
