# MNIST initial runs

When we list runs for a directory containing a guildfile, the runs are
limited to those that were generated from that guildfile.

Let's show runs for the MNIST example:

    >>> run("guild -C examples/mnist2 runs", ignore="FutureWarning")
    Limiting runs to 'examples/mnist2' (use --all to include all)
    <exit 0>

We can alternatively change to that directory and see the same results:

    >>> cd("examples/mnist2")
    >>> run("guild runs", ignore="FutureWarning")
    Limiting runs to the current directory (use --all to include all)
    <exit 0>

Note that Guild prints a message letting the user know the results are
limited.
