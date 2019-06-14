# TF Events

TF events are logged using `tensorboardX.SummaryWriter`.

    >>> import tensorboardX

We'll create our events log in a temp diretory:

    >>> logdir = mkdtemp()
    >>> dir(logdir)
    []

Our writer:

    >>> writer = tensorboardX.SummaryWriter(logdir)

We can use writer to write scalars:

    >>> writer.add_scalar("a", 1.0)
    >>> writer.add_scalar("b", 2.0)
    >>> writer.add_scalar("c", 3.0)

and close the writer:

    >>> writer.close()

The logdir:

    >>> logged = dir(logdir)
    >>> logged
    ['events.out.tfevents...']

The `tensorboardX` interface is write only. We can read the events
using `guild.tfevent.ScalarReader` to read back scalars:

    >>> from guild import tfevent
    >>> reader = tfevent.ScalarReader(logdir)
    >>> list(reader)
    [('a', 1.0, 0),
     ('b', 2.0, 0),
     ('c', 3.0, 0)]
