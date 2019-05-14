# API2

The `_api2` module provides an alternative interface to Guild
operations that is Notebook friendly.

    >>> from guild import _api2
    >>> from guild import config

Create a Guild home for our tests:

    >>> home = mkdtemp()

Define a simple function to run:

    >>> def hello(msg, n=3):
    ...     import sys
    ...     for i in range(n):
    ...         sys.stdout.write("%s %i!\n" % (msg, i + 1))

Run the function as an operation:

    >>> with config.SetGuildHome(home):
    ...     run, result = _api2.run(hello, msg="Hello")
    Hello 1!
    Hello 2!
    Hello 3!

    >>> run
    <guild.run.Run '...'>

    >>> print(result)
    None

    >>> cat(run.guild_path("output"))
    Hello 1!
    Hello 2!
    Hello 3!

List runs:

    >>> with config.SetGuildHome(home):
    ...     _api2.runs()
       run  operation  started     status
    0  ...    hello()      ...  completed

Print latest run info:

    >>> with config.SetGuildHome(home):
    ...     _api2.runs().info()
    id: ...
    operation: hello()
    status: completed
    started: ...
    stopped: ...
    label:
    run_dir: ...
    flags:
      msg: Hello
    <BLANKLINE>
