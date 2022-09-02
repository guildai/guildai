# Filter runs

Runs can be selected using text expressions. This support is provided
by the `guild.filter` module. In particular,
`guild.filter.runs_filter` generates a function that returns True if a
run matches a specified filter expression.

    >>> from guild.filter import runs_filter

For our tests, we use the `var` module to list runs. Runs can be
filtered using a function.

    >>> from guild import var

Let's create a helper function to print runs from the 'samples'
directory, filtered with an expression.

    >>> def filter(expr):
    ...     runs = var.runs(
    ...         sample("filter-runs"),
    ...         sort=["-started"],
    ...         filter=runs_filter(expr))
    ...     print_runs(runs, short_ids=True, labels=True, scalars=True)

The wildcard char matches any run:

    >>> filter("*")
    util:test  e394b696  target=fe83a924   loss=0.52803
    util:test  a5520d13  target=2dc1529b   loss=0.47875
    train      2dc1529b  noise=0.1 x=1.1   loss=0.47875
    train      79ca9e64  noise=0.1 x=0.1   loss=0.43514
    train      fe83a924  noise=0.1 x=-1.0  loss=0.52803

    >>> filter("x=1.1")
    train  2dc1529b  noise=0.1 x=1.1  loss=0.47875

    >>> filter("noise=0.1")
    train  2dc1529b  noise=0.1 x=1.1   loss=0.47875
    train  79ca9e64  noise=0.1 x=0.1   loss=0.43514
    train  fe83a924  noise=0.1 x=-1.0  loss=0.52803

    >> filter("flag:a=1 and flag:b=4")

    >> filter("status=completed or status=terminated")
    >> filter("attr:status=completed or attr:status=terminated")

    >> filter("loss<0.456 and acc>0.7")

    >> filter("scalar:loss<0.456 and scalar:acc>0.7")
