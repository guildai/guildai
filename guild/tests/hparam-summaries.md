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

    >>> monitor = RunsMonitor(logdir, list_runs_cb, log_images=False)

The monitor is designed to run a thread but we can run it preemptively
by calling `run_once`.

    >>> monitor.run_once()

The monitor generates files under the log directory. These include
links to run event logs and hparam specific files.

Because '...' will match multiple lines, we assert the file count.

    >>> files = findl(logdir)
    >>> len(files), files
    (3, ...)

And the files:

    >>> files
    ['... echo.py ... x_flag=1.123/.guild/events.out.tfevents.0000000000.hparams',
     '... echo.py ... x_flag=1.123/.guild/events.out.tfevents...',
     '... echo.py ... x_flag=1.123/.guild/events.out.tfevents.9999999999.time']

The first file contains the hparam experiment and session info.

    >>> islink(path(logdir, files[0]))
    False

The second file is a link to the run summaries.

    >>> islink(path(logdir, files[1]))
    True

Let's first look at the summaries. We'll use an event reader.

    >>> from guild.tfevent import EventReader

All of the events are written under the run logdir.

    >>> run_logdir = path(logdir, dirname(files[1]))

The events:

    >>> for event in EventReader(run_logdir):
    ...     print(event)
    summary {
      value {
        tag: "_hparams_/experiment"...
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
        tag: "_hparams_/session_start_info"...
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
        tag: "_hparams_/session_end_info"...
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
        tag: "x_metric"
        simple_value: 1.123...
      }
    }
    <BLANKLINE>
    summary {
      value {
        tag: "time"
        simple_value: ...
      }
    }
