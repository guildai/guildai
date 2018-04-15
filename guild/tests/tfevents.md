# TF Events

TF events can be logged using `guild.op_util.TFEvents`.

    >>> from guild import op_util

We'll create our events log in a temp diretory:

    >>> logdir = mkdtemp()
    >>> dir(logdir)
    []

Our events log:

    >>> events = op_util.TFEvents(logdir)

We can use events to log scalar summaries:

    >>> events.add_scalars([("a", 1.0), ("b", 2.0), ("c", 3.0)])

and close the events:

    >>> events.close()

The logdir:

    >>> logged = dir(logdir)
    >>> logged
    ['events.out.tfevents...']

The TFEvents interface is write only. We can read the summaries back
using a TensorBoard utility.

    >>> from tensorboard.backend.event_processing import event_file_loader
    >>> tf_events_path = join_path(logdir, logged[0])
    >>> loader = event_file_loader.EventFileLoader(tf_events_path)
    >>> for event in loader.Load():
    ...     if event.HasField("summary"):
    ...         for val in event.summary.value:
    ...             print((int(event.step), val.tag, val.simple_value))
    (0, u'a', 1.0)
    (0, u'b', 2.0)
    (0, u'c', 3.0)
