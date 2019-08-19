# HParam Summaries

Guild supports generation of hyperparameter (HParam) summaries when
viewing runs in TensorBoard. Guild writes HParam summaries for each
run, which contain information about flags and metrics (root scalars -
i.e. scalars that do not contain '/' chars). This information is used
by TensorBoard's HParams plugin.

To illustrate we'll use the `hparam-summaries` project.

    >>> project = Project(sample("projects", "hparam-summaries"))

The `echo.py` script simply logs a flag `x_flag` as an output scalar
`x_metric`.

    >>> project.run("echo.py", {"x_flag": 1.123})
    x_metric: 1.123

The runs monitor support in `guild.tensorboard` is used to generate
summary event logs for runs.

    >>> from guild.tensorboard import RunsMonitor

The monitor generates ephemeral event logs in a log directory.

    >>> logdir = mkdtemp()

The monitor needs a callback for listing runs. We'll use the project.

    >>> list_runs_cb = project.list_runs

And our monitor, configured to log only hparams:

    >>> monitor = RunsMonitor(logdir, list_runs_cb, logspec=["hparams"])

The monitor is designed to run a thread but we can run it preemptively
by calling `run_once`.

We wait a second to ensure that any logged summaries have a later
timestamp.

    >>> sleep(1)

And run the monitor:

    >>> monitor.run_once()

The monitor generates a number of files in the log directory. These
include links to run event logs as well as hparam specific files.

Because generated file names are non-deterministic (they include
randomly generated IDs and hashes) we need a method of sorting them
that presents the files in a consistent order.

    >>> def sort_files(paths, root):
    ...     def sort_key(subpath):
    ...         return subpath.count(os.path.sep), subpath
    ...     return sorted(paths, key=sort_key)

Here are the generated files:

    >>> files = sort_files(findl(logdir), logdir)

Because '...' will match multiple lines, let's assert the file count.

    >>> len(files), files
    (4, ...)

And the files:

    >>> files
    ['events.out.tfevents...',
     '... echo.py ... x_flag=1.123/events.out.tfevents...',
     '... echo.py ... x_flag=1.123/events.out.tfevents...',
     '... echo.py ... x_flag=1.123/.guild/hparams']

Experiment summaries for all of the runs first returned by the runs
callback function - in this case, all of our project runs - are
located in the log directory root.

Let's first look at the experiment summaries. We'll use an event reader.

    >>> from guild.tfevent import EventReader

    >>> for event in EventReader(logdir):
    ...     print(event)
    summary {
      value {
        tag: "_hparams_/experiment"
        metadata {
          plugin_data {
            plugin_name: "hparams"
            content: "..."
          }
        }
      }
    }

This event records the experiment info for all of the initial
runs. This information includes the run flags as hyperparameters and
root scalars (scalars that don't contain a '/' character) as metrics.

The run specific files under the log directory, in order listed above,
consist of:

 - Linked summaries log from the run directory
 - HParam session info
 - Marker that designates that the session info was written

 The first file is a link to the run scalars.

     >>> islink(path(logdir, files[1]))
     True

The second file is the monitor-generated summary log containing the
hparam session info.

    >>> islink(path(logdir, files[2]))
    False

The third files is a marked and is empty.

    >>> cat(path(logdir, files[3]))
    <empty>

The run log directly therefore contains both the run scalars and the
hparam session info.

    >>> run_logdir = path(logdir, dirname(files[1]))
    >>> for event in EventReader(run_logdir):
    ...     print(event)
    summary {
      value {
        tag: "x_metric"
        simple_value: 1.1230...
      }
    }
    <BLANKLINE>
    summary {
      value {
        tag: "_hparams_/session_start_info"
        metadata {
          plugin_data {
            plugin_name: "hparams"
            content: "..."
          }
        }
      }
    }
    <BLANKLINE>
    summary {
      value {
        tag: "_hparams_/session_end_info"
        metadata {
          plugin_data {
            plugin_name: "hparams"
            content: "..."
          }
        }
      }
    }
