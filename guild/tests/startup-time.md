# Startup Time

Guild should start within an acceptable amount of time. This test
measures the time it takes to run the `guild` command with no
arguments.

Our test limit:

    >>> START_THRESHOLD = float(os.getenv("GUILD_START_THRESHOLD") or 0.2)

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

Expected output (Guidl help):

    >>> print(out.decode())
    Usage: main_bootstrap.py [OPTIONS] COMMAND [ARGS]...
    <BLANKLINE>
      Guild AI command line interface.
    <BLANKLINE>
    Options:
      --version  Show the version and exit.
      -C PATH    Use PATH as current directory for referencing guild files
                 (guild.yml).
      -H PATH    Use PATH as Guild home (default is ...).
      --debug    Log more information during command.
      --help     Show this message and exit.
    <BLANKLINE>
    Commands:
      cat              Show contents of a run file.
      check            Check the Guild setup.
      comment          Add or remove run comments.
      compare          Compare run results.
      completion       Generate command completion script.
      diff             Diff two runs.
      download         Download a file resource.
      export           Export one or more runs.
      help             Show help for a path or package.
      import           Import one or more runs from ARCHIVE.
      init             Initialize a Guild environment.
      install          Install one or more packages.
      label            Set run labels.
      ls               List run files.
      mark             Mark a run.
      models           Show available models.
      open             Open a run path or output.
      operations, ops  Show model operations.
      package          Create a package for distribution.
      packages         Show or manage packages.
      publish          Publish one or more runs.
      pull             Copy one or more runs from a remote location.
      push             Copy one or more runs to a remote location.
      remote           Manage remote status.
      remotes          Show available remotes.
      run              Run an operation.
      runs             Show or manage runs.
      search           Search for a package.
      select           Select a run and shows its ID.
      shell            Start a Python shell for API use.
      stop             Stop one or more runs.
      sync             Synchronize remote runs.
      sys              System utilities.
      tag              Add or remove run tags.
      tensorboard      Visualize runs with TensorBoard.
      tensorflow       Collection of TensorFlow tools.
      uninstall        Uninstall one or more packages.
      view             Visualize runs in a local web application.
      watch            Watch run output.

Our run time for the `guild` command:

    >>> run_time = time1 - time0
    >>> run_time <= START_THRESHOLD, run_time
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
