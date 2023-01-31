# Long Run Names

These tests illustrate Guild's handling of runs that have long
names. A long name in this case is a name that cannot be used as-is in
a file system path.

File systems on Windows and POSIX systems have limits on file name
lengths. Default run names, which are not truncated to be legal file
system names, will cause errors when written.

Generate a run with a very long flag value. In this case, the script
`test.py` in the `long-run-names` sample project defines a value for
flag `foo` that's 374 chars long.

    >>> project = Project(sample("projects", "long-run-names"))
    >>> project.run("test.py")
    len_foo: 374
    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...

If the default run name, which would contain the full flag value for
`foo`, was used in a file system path, an error would be generated.

Let's illustrate using a temp directory.

    >>> tmp = mkdtemp()
    
    >>> open(join_path(tmp, "a" * 374), "w").close()  # doctest: +WINDOWS_ONLY
    Traceback (most recent call last):
    FileNotFoundError: [Errno 2] No such file or directory: '...aaaaaaaaaaaaaaaaaaaaaa'

    >>> open(join_path(tmp, "a" * 374), "w").close()  # doctest: -WINDOWS
    Traceback (most recent call last):
    OSError: [Errno ...] File name too long: '...aaaaaaaaaaaaaaaaaaaaaaaaaaa'

Runs monitor support handles this problem by truncating the run path
to fit within the system limits.

Let's illustrate by creating a runs monitor and running it once.

We need a callback to list available runs:

    >>> list_runs_cb = project.list_runs

We use a refresh callback, which is called by the runs monitor, to get
information about the runs the monitor processes. In this case, we add
the processed run to a `got_runs` list.

    >>> got_runs = []
    >>> def refresh_runs_cb(run, run_path):
    ...     got_runs.append((run, run_path))

Use a new temp directory for the log directory.

    >>> logdir = mkdtemp()

Create the monitor and run it once.

    >>> from guild import run_util
    >>> monitor = run_util.RunsMonitor(logdir, list_runs_cb, refresh_runs_cb)
    >>> monitor.run_once()

After processing the runs, we should now have one run.

    >>> len(got_runs)
    1

    >>> run, run_path = got_runs[0]

The run we got is the run we ran earlier.

    >>> run.id == project.list_runs()[0].id
    True

The default run name is too long.

    >>> default_path = join_path(logdir, run_util.default_run_name(run))
    >>> len(default_path) > run_util.MAX_RUN_PATH_LEN, default_path
    (True, ...)

When we compare the actual run path length, it's less than the default path length.

    >>> len(run_path) < len(default_path), (run_path, default_path)
    (True, ...)

In fact, the used run path is truncated to match the max run path length.

    >>> len(run_path) == run_util.MAX_RUN_PATH_LEN, run_path
    (True, ...)
