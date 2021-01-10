# Run in background

    >>> tmp = mkdtemp()
    >>> write(path(tmp, "sleep.py") , """
    ... import time
    ... i = 0
    ... while True:
    ...     print(i)
    ...     i += 1
    ...     time.sleep(1)
    ... """)

## Generated pidfile

Run in background - Guild chooses a pidfile.

    >>> run("guild -C '%s' run sleep.py --background -y" % tmp)
    sleep.py started in background as ... (pidfile ...)
    <exit 0>

Wait for operation to run for a few seconds.

    >>> sleep(3)

Stop the operation (defaults to the running operation).

    >>> run("guild stop -y")
    Stopping ... (pid ...)
    <exit 0>

Show the run output.

    >>> run("guild cat --output")
    0
    1
    ...
    <exit 0>

## Explicit pidfile

Run with an explicit pidfile.

    >>> run("guild -C '%s' run sleep.py --pidfile %s/PIDFILE -y" % (tmp, tmp))
    sleep.py started in background as ... (pidfile .../PIDFILE)
    <exit 0>

Guild uses the specified pidfile.

    >>> cat(path(tmp, "PIDFILE"))
    ???

Wait for the operation to run.

    >>> sleep(3)

Stop the operation (defaults to the running operation).

    >>> run("guild stop -y")
    Stopping ... (pid ...)
    <exit 0>

Show the run output.

    >>> run("guild cat --output")
    0
    1
    ...
    <exit 0>

## Run steps in background

Tmp project directory:

    >>> tmp = mkdtemp()

Guild file that defines a steps operation:

    >>> write(path(tmp, "guild.yml"), """
    ... upstream:
    ...   main: guild.pass
    ... downstream:
    ...   main: guild.pass
    ...   requires:
    ...     - operation: upstream
    ... steps:
    ...   steps:
    ...     - upstream
    ...     - downstream
    ... """)

Run steps in the background::

    >>> run("guild -C '%s' run steps --background -y" % tmp)
    steps started in background as ... (pidfile ...)
    <exit 0>

Wait for operation:

    >>> run("guild watch", timeout=10)
    Watching run ...
    INFO: [guild] running upstream: upstream
    INFO: [guild] running downstream: downstream
    Resolving upstream dependency
    Using run ... for upstream resource
    WARNING: nothing resolved for operation:upstream
    Run ... stopped with a status of 'completed'
    <exit 0>

List runs:

    >>> run("guild -C '%s' runs --limit 3" % tmp)
    [1:...]  downstream  ...  completed  upstream=...
    [2:...]  upstream    ...  completed
    [3:...]  steps       ...  completed
    <exit 0>
