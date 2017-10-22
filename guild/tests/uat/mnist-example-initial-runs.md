# MNIST initial runs

    >>> cd("guild-examples/mnist2")

When we list runs for a directory containing a modelfile, the runs are
limited to those that were generated from that modelfile. In this case
we haven't trained anything for this modelfile so our list is empty.

Note we get a message from Guild letting us know that the list is
limited.

    >>> run("guild runs")
    Limiting runs to the current directory (use --all to include all)
    <exit 0>
