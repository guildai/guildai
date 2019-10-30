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

    >>> run("guild -C %s run sleep.py --background -y" % tmp, ignore="Refreshing")
    ???/sleep.py started in background as ... (pidfile ...)
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

    >>> run("guild -C %s run sleep.py --pidfile %s/PIDFILE -y" % (tmp, tmp))
    ???/sleep.py started in background as ... (pidfile .../PIDFILE)
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
