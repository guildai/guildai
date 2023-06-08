# Startup Time

Guild should start within an acceptable amount of time. This test
measures the time it takes to run the `guild` command with no
arguments.

Our test limit:

    >>> START_THRESHOLD = float(os.getenv("GUILD_START_THRESHOLD") or 0.15)

Imports used below:

    >>> import time
    >>> import subprocess

Run `guild.main_bootstrap` module with no arguments to test startup time.

    >>> env = dict(os.environ)
    >>> env["PYTHONPATH"] = os.path.pathsep.join(sys.path)
    >>> time0 = time.time()
    >>> try:
    ...     out = subprocess.check_output(
    ...         [sys.executable, "-m", "guild.main_bootstrap"],
    ...         env=env,
    ...         stderr=subprocess.STDOUT)
    ... except subprocess.CalledProcessError as e:
    ...     print(e.output)
    ...     print("<exit %i>" % e.returncode)
    >>> time1 = time.time()

Our run time for the `guild` command:

    >>> run_time = time1 - time0
    >>> run_time <= START_THRESHOLD, (run_time, START_THRESHOLD)
    (True, ...)

If this test fails, look at the following:

- Look for recently added import statements that can be moved into
  functions for lazy imports.

- Look for new code that is run during imports that can be run lazily.

- If running on a slow system, consider disabling the test.

- If `run_time` is close to `START_THRESHOLD` the result may be an
  anomaly - ignore the error and run the test again.

- If there's no way to keep startup time down, consider increasing
  START_THRESHOLD above.
