# TF Events

TF events can be logged using `guild.op_util.TFEvents`.

    >>> from guild import op_util

We'll create our events log in a temp diretory:

    >>> logdir = mkdtemp()
    >>> events = op_util.TFEvents(logdir)

We can use events to log scalar summaries:

    >>> events.add_scalars([("a", 1.0), ("b", 2.0), ("c", 3.0)])

and close the events:

    >>> events.close()

The TFEvents interface is write only. We can read the summaries back
using a TensorBoard utility.

    >>> from tensorboard.backend.event_processing import event_accumulator
    >>> tb_events = event_accumulator._GeneratorFromPath(logdir)
    >>> for event in tb_events.Load():
    ...     if event.HasField("summary"):
    ...         for val in event.summary.value:
    ...             print((event.step, val.tag, val.simple_value))
    (0L, u'a', 1.0)
    (0L, u'b', 2.0)
    (0L, u'c', 3.0)
