# TensorBoard Plugin

    >>> from guild.plugins import tensorboard as tb

    >>> tb.version()
    '2.3.0'

    >>> tb.version_supported()
    True

## Silence TensorBoard logging

TensorBoard assumes that it's running as a standalone app and so logs
vociferously.

    >>> tb.silence_info_logging()

## Summaries

Simple value (used for scalars):

    >>> tb.Summary("tag", simple_value=1.123)
    value {
      tag: "tag"
      simple_value: 1.123000...
    }
    <BLANKLINE>

Images:

    >>> img_bytes = open(sample("projects", "image-summaries", "pixel.png"),
    ...                  "rb").read()
    >>> tb.Image(
    ...    height=1,
    ...    width=1,
    ...    encoded_image_string=img_bytes,
    ... )
    height: 1
    width: 1
    encoded_image_string: "\211PNG\r\n..."


## Events

    >>> tb.Event(file_version="brain.Event:2")
    file_version: "brain.Event:2"

    >>> tb.Event(summary=tb.Summary("tag", simple_value=1.123), step=100)
    step: 100
    summary {
      value {
        tag: "tag"
        simple_value: 1.123000...
      }
    }


## AsyncWriter

Helper to generate serialized summary event.

    >>> def summary_event(tag, value, step):
    ...     event = tb.Event(
    ...         summary=tb.Summary(tag=tag, simple_value=value),
    ...         step=step)
    ...     return event.SerializeToString()

Write some events to a log dir.

    >>> logdir = mkdtemp()

    >>> writer = tb.AsyncWriter(logdir, filename_base="tests")
    >>> writer.write(summary_event("loss", 10, 1))
    >>> writer.flush()  # Call flush to confirm the API.
    >>> writer.write(summary_event("loss", 5, 2))
    >>> writer.write(summary_event("loss", 1, 3))
    >>> writer.close()

Show the log dir files.

    >>> dir(logdir)
    ['events.out.tfevents.tests']

Read the events.

    >>> for event in tb.iter_tf_events(logdir):
    ...     print(event)
    step: 1
    summary {
      value {
        tag: "loss"
        simple_value: 10.0
      }
    }
    <BLANKLINE>
    step: 2
    summary {
      value {
        tag: "loss"
        simple_value: 5.0
      }
    }
    <BLANKLINE>
    step: 3
    summary {
      value {
        tag: "loss"
        simple_value: 1.0
      }
    }

Util to generate event file names.

    >>> tb.event_filename("logdir")
    'logdir/events.out.tfevents...'

    >>> tb.event_filename("logdir", filename_suffix=".tests")
    'logdir/events.out.tfevents....tests'

    >>> tb.event_filename("logdir", filename_base="tests")
    'logdir/events.out.tfevents.tests'

    >>> tb.event_filename("logdir", filename_base="tests", filename_suffix=".1")
    'logdir/events.out.tfevents.tests.1'

## Access to proto interfaces

    >>> tb.hparams_hp_proto()
    <module 'tensorboard.plugins.hparams.summary_v2' ...>

    >>> tb.hparams_api_proto()
    <module 'tensorboard.plugins.hparams.api_pb2' ...>

## TensorBoard WSGI app

Get base plugins.

    >>> plugins = tb.base_plugins()

    >>> for name in sorted([p.__name__ for p in plugins]):
    ...     print(name)  # doctest: +REPORT_UDIFF
    AudioPlugin
    BeholderPluginLoader
    CorePluginLoader
    CustomScalarsPlugin
    DebuggerPluginLoader
    DebuggerV2Plugin
    DistributionsPlugin
    ExperimentalNpmiPlugin
    ExperimentalTextV2Plugin
    GraphsPlugin
    HParamsPlugin
    HistogramsPlugin
    ImagesPlugin
    MeshPlugin
    PrCurvesPlugin
    ProfileRedirectPluginLoader
    ProjectorPlugin
    ScalarsPlugin
    TextPlugin
    WhatIfToolPluginLoader

Create WSGI app.

    >>> tb.wsgi_app(logdir, plugins)
    <tensorboard.backend.application.TensorBoardWSGI ...>
