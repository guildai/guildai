# API2

The `_api2` module provides an alternative interface to Guild
operations that is Notebook friendly.

    >>> from guild import _api2
    >>> from guild import config

Create a Guild home for our tests:

    >>> guild_home = config.SetGuildHome(mkdtemp())

Define a simple function to run:

    >>> def hello(msg, n=3):
    ...     import sys
    ...     for i in range(n):
    ...         sys.stdout.write("%s %i!\n" % (msg, i + 1))

## Running an operation

The `_api2` interface runs operations as Python functions. Flags are
provided as key words:

    >>> with guild_home:
    ...     run, result = _api2.run(hello, msg="Hello")
    Hello 1!
    Hello 2!
    Hello 3!

    >>> run
    <guild.run.Run '...'>

    >>> print(result)
    None

Files:

    >>> find(run.path)
    ['.guild/attrs/exit_status',
     '.guild/attrs/flags',
     '.guild/attrs/id',
     '.guild/attrs/initialized',
     '.guild/attrs/started',
     '.guild/attrs/stopped',
     '.guild/opref',
     '.guild/output']

Output:

    >>> cat(run.guild_path("output"))
    Hello 1!
    Hello 2!
    Hello 3!

Run another operation:

    >>> with guild_home:
    ...     _api2.run(hello, msg="Hola", n=2)
    Hola 1!
    Hola 2!
    (<guild.run.Run '...'>, None)

## List runs

List runs:

    >>> with guild_home:
    ...     _api2.runs()
       run  operation  started     status
    0  ...    hello()      ...  completed
    1  ...    hello()      ...  completed

## Runs info

Print latest run info:

    >>> with guild_home:
    ...     _api2.runs().info()
    id: ...
    operation: hello()
    status: completed
    started: ...
    stopped: ...
    label:
    run_dir: ...
    flags:
      msg: Hola
      n: 2
    <BLANKLINE>

Info for a specific run:

    >>> with guild_home:
    ...     _api2.runs().iloc[1].info()
    id: ...
    operation: hello()
    status: completed
    started: ...
    stopped: ...
    label:
    run_dir: ...
    flags:
      msg: Hello

## Flags

Flags can be read as a data frame using the `flags()` function on runs.

    >>> with guild_home:
    ...     runs = _api2.runs()

    >>> flags = runs.flags()

    >>> flags
         msg    n  run
    0   Hola  2.0  ...
    1  Hello  NaN  ...

    >>> pprint(flags.to_dict("records"))
    [{'msg': 'Hola', 'n': 2.0, 'run': '...'},
     {'msg': 'Hello', 'n': nan, 'run': '...'}]

## Delete runs

Delete runs:

    >>> with guild_home:
    ...     _api2.runs().delete()
    ['...', '...']

    >>> with guild_home:
    ...     _api2.runs()
    Empty RunsDataFrame
    Columns: [run, operation, started, status]
    Index: []

Deleting an empty list:

    >>> with guild_home:
    ...     _api2.runs().delete()
    []

## Logging scalars

The `_api2` interface does not provide an explicit interface for
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

With these points in mind, `_api2` supports scalar logging in two ways:

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
    ...     run, _result = _api2.run(op1, a=1, b=2)
    x: 3
    y: -1
    z: 1

Files:

    >>> find(run.path)
    ['.guild/attrs/exit_status',
     '.guild/attrs/flags',
     '.guild/attrs/id',
     '.guild/attrs/initialized',
     '.guild/attrs/started',
     '.guild/attrs/stopped',
     '.guild/events.out.tfevents...',
     '.guild/opref',
     '.guild/output']

Note that output now contains a `tsevents` file.

Read the scalars:

    >>> with guild_home:
    ...     scalars = _api2.runs().scalars()

    >>> scalars
       avg_val  count  first_step  ...  run  tag  total
    0      3.0      1           0  ...  ...    x    3.0
    1     -1.0      1           0  ...  ...    y   -1.0
    2      1.0      1           0  ...  ...    z    1.0
    <BLANKLINE>
    [3 rows x 14 columns]

    >>> scalars[["run", "last_step", "last_val"]]
       run  last_step  last_val
    0  ...          0       3.0
    1  ...          0      -1.0
    2  ...          0       1.0

### Logging scalars as TFEvents

This function uses tensorboardX to write scalars.

    >>> def op2(a, c):
    ...     import tensorboardX
    ...     writer = tensorboardX.SummaryWriter(".")
    ...     writer.add_scalar("x", a + c, 1)
    ...     writer.add_scalar("x", a + c + 1, 2)
    ...     writer.add_scalar("x", a + c + 2, 3)
    ...     writer.close()

Let's run the function as an operation:

    >>> with guild_home:
    ...     run, _result = _api2.run(op2, a=1.0, c=0.0)

The run files:

    >>> find(run.path)
    ['.guild/attrs/exit_status',
     '.guild/attrs/flags',
     '.guild/attrs/id',
     '.guild/attrs/initialized',
     '.guild/attrs/started',
     '.guild/attrs/stopped',
     '.guild/opref',
     '.guild/output',
     'events.out.tfevents...']

And its scalars:

    >>> with guild_home:
    ...     runs = _api2.runs()
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
      'prefix': u'',
      'run': u'...',
      'tag': u'x',
      'total': 6.0}]

## Comparing runs

The `compare()` function can be applied to a list of runs to return a
data frame that has both flags and scalars.

    >>> with guild_home:
    ...     runs = _api2.runs()

    >>> compare = runs.compare()

    >>> compare
         a    b    c  run  step    x    y    z
    0  1.0  NaN  0.0  ...     3  3.0  NaN  NaN
    1  1.0  2.0  NaN  ...     0  3.0 -1.0  1.0
