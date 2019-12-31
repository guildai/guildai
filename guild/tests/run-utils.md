# Run Utils

The `run_util` module provides various run related utility functions.

    >>> from guild import run_util

## Formatting run attributes

    >>> def fmt(val):
    ...     print(run_util.format_attr(val))

    >>> fmt("1")
    1

    >>> fmt("1.1")
    1.1

    >>> fmt(True)
    yes

    >>> fmt("10")
    10

    >>> fmt([1, 2, "a b", 1/6])
    <BLANKLINE>
      1
      2
      a b
      0.16666666666666666

    >>> fmt({
    ...   "a": "A",
    ...   "b": 1.1,
    ...   "c": 1e100,
    ... })
    <BLANKLINE>
      a: A
      b: 1.1
      c: 1.0e+100

## Monitoring runs

The class `run_util.RunsMonitor` is responsible for monitoring runs
and maintaining parallel directories under a log directory.

The monitor gets runs from a callback function. It calls this function
at a set interval to get the latest set of runs and updates its log
directory accordingly.

When the monitor refresh its list of runs, it uses another callback
function to indicate that a run needs to be refreshed.

For our tests we'll use a run proxy that provides the information used
by the monitor.

    >>> class RunProxy(object):
    ...
    ...     def __init__(self, id, op_name, started, label):
    ...         from guild.opref import OpRef
    ...         self.short_id = id
    ...         self.opref = OpRef.for_string(op_name)
    ...         self.attrs = {
    ...             "started": started,
    ...             "label": label,
    ...         }
    ...         self.get = self.attrs.get

Here's a callback that returns a sample list of runs:

    >>> sample_runs = [
    ...     RunProxy("aaaa", "op-1", 1565989068985148, None),
    ...     RunProxy("bbbb", "op-2", 1565989403019750, "a label"),
    ... ]

    >>> sample_runs_cb = lambda: sample_runs

Here's our refresh run callback:

    >>> def refresh_run_cb(run, path):
    ...     print("<refresh %s in %s>" % (run.short_id, basename(path)))

A run monitor is design to run automatically in a thread, however, we
can run it preemptively by calling its `run_once` method, which runs
in the current thread.

Let's create a log directory:

    >>> logdir = mkdtemp()

And our monitor:

    >>> monitor = run_util.RunsMonitor(logdir, sample_runs_cb, refresh_run_cb)

Let's run the monitor once:

    >>> monitor.run_once()
    <refresh aaaa in aaaa op-1 2019-08-16 ...57...48>
    <refresh bbbb in bbbb op-2 2019-08-16 ...03...23 a label>

The step of instantiating monitor results in runs being created in the
log directory.

    >>> names = dir(logdir)
    >>> names
    ['aaaa op-1 2019-08-16 ...57...48',
     'bbbb op-2 2019-08-16 ...03...23 a label']

The directory structure does not contain any files.

    >>> find(logdir)  # only shows files, not directories
    <empty>

We can add files to any of the run directories.

    >>> touch(path(logdir, names[0], "a-file"))
    >>> touch(path(logdir, names[1], "b-file"))

    >>> find(logdir)
    aaaa op-1 2019-08-16 ...57...48/a-file
    bbbb op-2 2019-08-16 ...03...23 a label/b-file

The monitor is designed to be started as a thread, where it monitors
the list of runs from its callback and updates the log directory
accordingly. We can preemptively update the log directory by calling
`run_once()`.

### Deleted runs

Let's simulate the deletion of run `bbbb` by removing it from the list
of sample runs:

    >>> run_bbbb = sample_runs.pop()

Next we'll call `run_once()` on our monitor to update the log
directory.

    >>> monitor.run_once()
    <refresh aaaa in aaaa op-1 2019-08-16 ...57...48>

Our new list of runs:

    >>> dir(logdir)
    ['aaaa op-1 2019-08-16 ...57...48']

And files:

    >>> find(logdir)
    aaaa op-1 2019-08-16 ...57...48/a-file

### Added runs

Let's add run `bbbb` back and repeat this process.

    >>> sample_runs.append(run_bbbb)

    >>> monitor.run_once()
    <refresh aaaa in aaaa op-1 2019-08-16 ...57...48>
    <refresh bbbb in bbbb op-2 2019-08-16 ...03...23 a label>

    >>> runs = dir(logdir)
    >>> runs
    ['aaaa op-1 2019-08-16 ...57...48',
     'bbbb op-2 2019-08-16 ...03...23 a label']

    >>> find(logdir)
    aaaa op-1 2019-08-16 ...57...48/a-file

Note that `b-file` is not restored. The monitor permanently deletes
directories associated with deleted runs.

Let's restore `b-file`:

    >>> touch(path(logdir, runs[1], "b-file"))

    >>> find(logdir)
    aaaa op-1 2019-08-16 ...57...48/a-file
    bbbb op-2 2019-08-16 ...03...23 a label/b-file

### Modified run labels

Let's now modify the label of run `bbbb`.

    >>> sample_runs[1].attrs["label"] = "modified label"

And update the log directory.

    >>> monitor.run_once()
    <refresh aaaa in aaaa op-1 2019-08-16 ...57...48>
    <refresh bbbb in bbbb op-2 2019-08-16 ...03...23 modified label>

Here are the new runs:

    >>> dir(logdir)
    ['aaaa op-1 2019-08-16 ...57...48',
     'bbbb op-2 2019-08-16 ...03...23 modified label']

And files:

    >>> find(logdir)
    aaaa op-1 2019-08-16 ...57...48/a-file

Once again, `b-file` is deleted. The monitor identifies runs by their
name. When we changed the label, we changed the generated name for the
run. The model interprets that as a deleted run (the original name)
and a new run (the new name).

### Max run names

The default run name function shortens long names by truncating them
to fit within `run_util.MAX_RUN_NAME_LEN`.

Here's a run with a long label:

    >>> long_label = "a" * run_util.MAX_RUN_NAME_LEN + "<eol>"
    >>> sample_runs.append(RunProxy("cccc", "op-2", 1577806744267292, long_label))

Run the monitor:

    >>> monitor.run_once()
    <refresh aaaa in aaaa op-1 2019-08-16 ...57...48>
    <refresh bbbb in bbbb op-2 2019-08-16 ...03...23 modified label>
    <refresh cccc in cccc op-2 2019-12-31 ...39...04 ...aaaaaaaaaaa>

Let's confirm that the name used for our long label run is within the
limit.

    >>> long_label_run_name = dir(logdir)[2]
    >>> long_label_run_name
    'cccc op-2 2019-12-31 ...39...04 ...aaaaaaaaaaaaaaaaaaaaaaaaaaaa'

    >>> len(long_label_run_name) <= run_util.MAX_RUN_NAME_LEN
    True
