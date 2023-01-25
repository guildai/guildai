# Dask Basics

We use the `simple` project for our tests.

    >>> cd(sample("projects", "simple"))

Operation functions:

    >>> def op1():
    ...     return gapi.run_capture_output("simple", flags={"x": 1})

    >>> def op2():
    ...     return gapi.run_capture_output("simple", flags={"x": 2})

    >>> def op3():
    ...     return gapi.run_capture_output("simple", flags={"x": 3})

Run operations in series measuring time:

    >>> import time
    >>> t0 = time.time()
    >>> print(op1())
    x: 1
    y: 2
    <BLANKLINE>

    >>> print(op2())
    x: 2
    y: 3
    <BLANKLINE>

    >>> print(op3())
    x: 3
    y: 4
    <BLANKLINE>

    >>> series_time = time.time() - t0

Run operations using Dask measuring time.

    >>> import dask
    >>> from dask.distributed import Client, LocalCluster
    >>> from dask import delayed

    >>> temp_dir = mkdtemp("guild-dask-worker-space-")
    >>> with dask.config.set({"temporary-directory": temp_dir}):
    ...     # Capture log output to as cluster start/stop is noisy
    ...     with LogCapture() as _ignored:
    ...         cluster = LocalCluster(processes=False)
    ...         client = Client(cluster)
    ...         op1_out = delayed(op1)()
    ...         op2_out = delayed(op2)()
    ...         op3_out = delayed(op3)()
    ...         t0 = time.time()
    ...         results = delayed(lambda x: x)([op1_out, op2_out, op3_out]).compute()
    ...         cluster.close()
    >>> for out in results:
    ...     print(out)
    x: 1
    y: 2
    <BLANKLINE>
    x: 2
    y: 3
    <BLANKLINE>
    x: 3
    y: 4
    <BLANKLINE>

    >>> parallel_time = time.time() - t0

Cleanup:

    >>> client.close()
    >>> cluster.close()

Verify that `dask-worker-space` doesn't exit.

    >>> exists("dask-worker-space")
    False

Speed up:

    >>> speedup = series_time / parallel_time
    >>> speedup_min = float(os.getenv("DASK_SPEEDUP_THRESHOLD", 1.5))
    >>> speedup >= speedup_min, (speedup, speedup_min)
    (True, ...)
