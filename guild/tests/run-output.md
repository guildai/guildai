# Run output

Guild captures run output by logging it to an `output` file and also
indexing the output to capture time and stream.

Run output is managed by `guild.op_util.RunOutput`.

    >>> from guild import op_util

Run output is associated with a run. We'll use a temporary directory
to store our output.

    >>> run_dir = mkdtemp()

Our run:

    >>> import guild.run
    >>> run = guild.run.Run("test", run_dir)

To write guild files (under the run dir's `.guild` directory) we need
 to call `init_skel`.

    >>> run.init_skel()

We can now create our run output. For our tests, we can't write to
stdout because this would interfere with our test assertions (which
captures stdout as a part of a test). We can use the `quiet` arg to
skip writing to our output streams:

    >>> output = op_util.RunOutput(run, quiet=True)

Initially output is not opened:

    >>> output.closed
    True

Run output is opened with a process. We need a process that writes to
both stdout and stderr so we'll use pipes:

    >>> import subprocess, sys
    >>> proc = subprocess.Popen(
    ...   [sys.executable, "-u", sample("scripts/sample_run.py")],
    ...   stdout=subprocess.PIPE,
    ...   stderr=subprocess.PIPE)

At this point our process has started and we can open output with it.

    >>> output.open(proc)

Our output is now open:

    >>> output.closed
    False

To proceed, we can let the process run to completion by waiting for
it.

    >>> exit_status = proc.wait()

It should have succeeded!

    >>> exit_status
    0

We can now wait for our output to finish reading. We'll use the
convenience method `wait_and_close`, which also closes the output
after waiting:

    >>> output.wait_and_close()

Let's inspect our run output.

    >>> cat(run.guild_path("output"))
    This is to stdout
    This is to stderr
    This is delayed by 0.2 seconds
    <BLANKLINE>

We can use `util.RunOutputReader` to read back output with time and
stream info.

    >>> from guild.util import RunOutputReader
    >>> reader = RunOutputReader(run.path)
    >>> indexed = reader.read()
    >>> indexed
    [(..., 0, u'This is to stdout'),
     (..., 1, u'This is to stderr'),
     (..., 0, u'This is delayed by 0.2 seconds')]

Let's confirm that the last entry is in fact delayed.

    >>> delay = indexed[2][0] - indexed[1][0]
    >>> delay >= 200, delay
    (True, ...)
