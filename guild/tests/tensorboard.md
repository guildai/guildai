# TensorBoard

These are miscellaneous checks for TensorBoard support.

## TensorBoard compatibility

See `uat/tensorboard-versions.md` for TensorBoard version
compatibility tests.

## Runs Monitor

The class `guild.tensorboard.RunsMonitor` is responsible for running
in a background thread that monitors a list of runs and applies
changes as needed to a TB log directory.

    >>> from guild.tensorboard import RunsMonitor

We a log directory.

    >>> logdir = mkdtemp()

For our runs, we use the `tensorboard` project.

    >>> project = Project(sample("projects", "tensorboard"))

We can use the project `runs` method as the run callback for the
monitor.

We can also provide a function for naming the run directories the
monitor uses.

    >>> run_name = lambda run: "run-%s" % run.short_id

Our monitor:

    >>> monitor = RunsMonitor(logdir, project.list_runs, run_name_cb=run_name)

Run monitors are typically run in a polling thread. For our tests, we
use the `run_once` method to explicitly check each step of our tests.

Our log directory is initially empty.

    >>> find(logdir)
    <empty>

With no runs, there's nothing to setup.

    >>> with LogCapture(log_level=0) as log:
    ...     monitor.run_once()

    >>> log.print_all()
    DEBUG: [guild] Refreshing runs

    >>> find(logdir)
    <empty>

Let's run three sample operations.

    >>> project.run("op")
    m1: 1.123

    >>> project.run("op", flags={"a": 2.0, "c": "hola"})
    m1: 1.123

    >>> project.run("op", flags={"a": 3, "b": "3.0", "c": "bonjour"})
    m1: 1.123

    >>> project.print_runs(flags=True)
    op  a=3 b=3.0 c=bonjour d=yes extra_metrics=0
    op  a=2.0 b=2 c=hola d=yes extra_metrics=0
    op  a=1.0 b=2 c=hello d=yes extra_metrics=0

The combination of these runs defines the hyperparameters (hparams)
and metrics setup by the runs monitor. The hparam TB plugin does not
modify the hparam settings when it reads subsequent experiment
summaries. Any runs the monitor handles after this first set must fit
within the hparam domain scheme to be displayed as expected in the
hparam tab.

We run three runs of specific values to establish the following hparam
scheme:

- Flag `a` consists of three numbers, so is created as an unbounded
  `RealInterval` by the monitor.

- Flag `b` is of mixed type and so will not have a domain. The hparam
  interface does not support filtering or log scale options for
  hparams without a domain.

- Flag `c` consists of three strings: hello, hola, and bonjour. These
  are defined using a `Discrete` domain, which supports filtering by
  checking and unchecking values.

- Flag `d` conists only of boolean values and will be created with a
  special `Discrete` domain consisting of only True and False
  options. Note that even though False does not appear in any of the
  runs, the monitor adds it as an option.

Let's run the monitor, capturing debug output.

    >>> with LogCapture(log_level=0) as log:
    ...     monitor.run_once()

The monitor generates the following logs:

    >>> log.print_all()
    DEBUG: [guild] Refreshing runs
    DEBUG: [guild] hparam experiment:
           hparams=['a', 'b', 'c', 'd', 'extra_metrics', 'sourcecode']
           metrics=['m1', 'time']
    DEBUG: [guild] Creating link from '.../.guild/events.out.tfevents...' to '.../.guild/events.out.tfevents...'
    DEBUG: [guild] hparam experiment:
           hparams=['a', 'b', 'c', 'd', 'extra_metrics', 'sourcecode']
           metrics=['m1', 'time']
    DEBUG: [guild] Creating link from '.../.guild/events.out.tfevents...' to '.../.guild/events.out.tfevents...'
    DEBUG: [guild] hparam experiment:
           hparams=['a', 'b', 'c', 'd', 'extra_metrics', 'sourcecode']
           metrics=['m1', 'time']
    DEBUG: [guild] Creating link from '.../.guild/events.out.tfevents...' to '.../.guild/events.out.tfevents...'

Note the following from the log output:

- The experiment summaries are the same. Guild writes new summaries
  for each run using the combined information on hparms and metrics
  for all available runs.

- Each run events log is linked within the monitor log dir.

And the log dir:

    >>> find(logdir)
    run-.../.guild/events.out.tfevents.0000000000.hparams
    run-.../.guild/events.out.tfevents...
    run-.../.guild/events.out.tfevents.9999999999.time
    run-.../.guild/events.out.tfevents.0000000000.hparams
    run-.../.guild/events.out.tfevents...
    run-.../.guild/events.out.tfevents.9999999999.time
    run-.../.guild/events.out.tfevents.0000000000.hparams
    run-.../.guild/events.out.tfevents...
    run-.../.guild/events.out.tfevents.9999999999.time

For subsequent tests in this section we assert file count in logdir.

    >>> len(findl(logdir))
    9

Now the fun begins! Each new run that arrives may or may not fall
within the scheme inferred from the first set of runs. Runs that fall
within the scheme are logged without warning. Runs that do not
generate one or more warnings.

Let's generate a run that falls within the scheme, specifically:

- `a` is a number
- `b` is a number
- `c` is one of the three known string values
- `d` is boolean

    >>> project.run("op", flags={"a": 0, "b": 1, "c": "hola", "d": False})
    m1: 1.123

With this new run, let's run the monitor.

    >>> with LogCapture(log_level=0) as log:
    ...     monitor.run_once()

    >>> log.print_all()
    DEBUG: [guild] Refreshing runs
    DEBUG: [guild] hparam experiment:
           hparams=['a', 'b', 'c', 'd', 'extra_metrics', 'sourcecode']
           metrics=['m1', 'time']
    DEBUG: [guild] Creating link ...

Note the same hparam experiment scheme.

Next we generate a run that falls outside the scheme.

- `a` is not a number
- `c` is not one of the three original values
- `d` is not a boolean

We need to use force-flags because the values violate our operation
flag type constraints.

    >>> project.run("op", flags={"a": "zero", "c": "bye", "d": "a_str"}, force_flags=True)
    m1: 1.123

When we ask the monitor to process this run, it logs warnings about
each incompatibility.

    >>> with LogCapture(log_level=0) as log:
    ...     monitor.run_once()

    >>> log.print_all()
    DEBUG: [guild] Refreshing runs
    WARNING: Runs found with hyperparameter values that cannot be displayed in the
             HPARAMS plugin: a=zero, c=bye. Restart this command to view them.
    DEBUG: [guild] hparam experiment:
           hparams=['a', 'b', 'c', 'd', 'extra_metrics', 'sourcecode']
           metrics=['m1', 'time']
    DEBUG: [guild] Creating link ...

Next we generate a run with flags that weren't in the original set.

    >>> project.run("op", flags={"e": 123}, force_flags=True)
    m1: 1.123

In this case, the monitor warns of new hyperparameters.

    >>> with LogCapture(log_level=0) as log:
    ...     monitor.run_once()

    >>> log.print_all()
    DEBUG: [guild] Refreshing runs
    WARNING: Runs found with new hyperparameters: e. These hyperparameters
             will NOT appear in the HPARAMS plugin. Restart this command to view them.
    WARNING: Runs found with hyperparameter values that cannot be displayed in the
             HPARAMS plugin: a=zero, c=bye. Restart this command to view them.
    DEBUG: [guild] hparam experiment:
           hparams=['a', 'b', 'c', 'd', 'extra_metrics', 'sourcecode']
           metrics=['m1', 'time']
    DEBUG: [guild] Creating link ...

Note that the monitor warns of the full set of incompatible hparam
items - not just of the more recently added run. This is
less-than-ideal as it is preferable to include specific about each
run, but this approach is sufficient to call attention to the issue.

Finally, we generate a run that logs scalars that are not part of the
original set. This too causes the monitor to log a warning.

    >>> project.run("op", flags={"extra_metrics": 2})
    m1: 1.123
    m2: 1.123
    m3: 1.123

    >>> with LogCapture(log_level=0) as log:
    ...     monitor.run_once()

    >>> log.print_all()
    DEBUG: [guild] Refreshing runs
    WARNING: Runs found with new hyperparameters: e. These hyperparameters
             will NOT appear in the HPARAMS plugin. Restart this command to view them.
    WARNING: Runs found with hyperparameter values that cannot be displayed in the
             HPARAMS plugin: a=zero, c=bye. Restart this command to view them.
    WARNING: Runs found with new metrics: m2, m3. These runs will NOT appear in the
             HPARAMS plugin. Restart this command to view them.
    DEBUG: [guild] hparam experiment:
           hparams=['a', 'b', 'c', 'd', 'extra_metrics', 'sourcecode']
           metrics=['m1', 'time']
    DEBUG: [guild] Creating link ...

## Run names

The name shown in TensorBoard for a run is determined by a run name
callback function. If a callback is not provided, Guild generates a
value using run attributes including the run label.

Here's a monitor that uses the default name:

    >>> monitor = RunsMonitor(logdir, project.list_runs, run_name_cb=None)

Let's clear our runs.

    >>> project.delete_runs()
    ???

Generate a run and show monitor processing.

    >>> project.run("op")
    m1: 1.123

    >>> with LogCapture(log_level=0) as log:
    ...     monitor.run_once()

    >>> log.print_all()
    ???
    DEBUG: [guild] Creating link from '...' to '... op ... a=1.0 b=2 c=hello d=yes extra_metrics=0...'

Note the use of the flag assignments, which is the run label.

    >>> project.print_runs(labels=True)
    op  a=1.0 b=2 c=hello d=yes extra_metrics=0

Here's a custom run name callback function:

    >>> def run_name(run):
    ...     return "the run <%s>" % run.short_id

    >>> monitor = RunsMonitor(logdir, project.list_runs, run_name_cb=run_name)

Delete our runs again.

    >>> project.delete_runs()
    ???

Generate a run and show monitor processing.

    >>> project.run("op")
    m1: 1.123

    >>> with LogCapture(log_level=0) as log:
    ...     monitor.run_once()

    >>> log.print_all()  # doctest: -WINDOWS
    ???
    DEBUG: [guild] Creating link from '...' to '...the run <...>...'

    >>> log.print_all()  # doctest: +WINDOWS_ONLY
    ???
    DEBUG: [guild] Creating link from '...' to '...the run _..._...'

Guild provides a safe-guard against invalid DOM characters used in the
run name. This ensures that the run can be selected in TensorBoard UI
(see issue #230).

Here's a function that deliberately inserts a invalid DOM character
(an ellipsis).

    >>> def run_name(run):
    ...     return u"the run <%s> \u2026" % run.short_id

    >>> monitor = RunsMonitor(logdir, project.list_runs, run_name_cb=run_name)

Delete our runs.

    >>> project.delete_runs()
    ???

Generate a run and show monitor processing.

    >>> project.run("op")
    m1: 1.123

    >>> with LogCapture(log_level=0) as log:
    ...     monitor.run_once()

    >>> log.print_all()  # doctest: -WINDOWS
    ???
    DEBUG: [guild] Creating link from '...' to '...the run <...> ?...'

    >>> log.print_all()  # doctest: +WINDOWS_ONLY
    ???
    DEBUG: [guild] Creating link from '...' to '...the run _..._ _...'

## Misc Tests

Run label template for --run-name-flags arg:

    >>> from guild.commands import tensorboard_impl as impl

    >>> impl._run_label_template("")
    ''

    >>> impl._run_label_template("foo")
    'foo=${foo}'

    >>> impl._run_label_template("foo,bar")
    'foo=${foo} bar=${bar}'

    >>> impl._run_label_template("foo bar")
    'foo=${foo} bar=${bar}'

    >>> impl._run_label_template("  foo, bar,  ")
    'foo=${foo} bar=${bar}'
