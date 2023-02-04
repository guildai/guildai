---
doctest: +TIMING_CRITICAL
---

# Run stop after

The `--stop-after` run option tells Guild to stop a run after a
specified number of minutes.

We use the `repeat.py` script in the `hello` project to illustrate.

    >>> cd(example("hello"))

`repeat.py` prints a specified number of messages every second.

By default, Guild polls every 5 seconds when checking process status
to stop it.

Run `repeat.py`, printing 6 messages with a near immediate stop
time. Guild will wait 5 seconds before stopping the process, letting
the run print the message only 5 times rather than the expected 6.

    >>> run("guild run repeat.py repeat=6 --stop-after 0.01 -y")
    Hello Guild!
    Hello Guild!
    Hello Guild!
    Hello Guild!
    Hello Guild!
    Stopping process early (pid ...) - 0.1 minute(s) elapsed...
    <exit ...>
