# Steps with --restart

These steps extend those defined in [`steps.md`](steps.md) to
demonstrate Guild's behavior when restarting a pipeline.

Pipelines are commonly restarted when one or more steps fail.

Create and use a helper to initiliaze a fresh temporary project.

    >>> def use_tmp_project():
    ...     use_project(mkdtemp())
    ...
    ...     write("guild.yml", """
    ...     - model: m1
    ...       operations:
    ...         steps-restart:
    ...           flags:
    ...             fail: yes
    ...           steps:
    ...             - fail fail=no
    ...             - fail fail=${fail}
    ...         steps-validation-error:
    ...           flags:
    ...             fail: yes
    ...           steps:
    ...             - fail fail=no validation.error=yes
    ...             - fail fail=${fail}
    ...         fail:
    ...           flags-import: all
    ...     """)
    ...
    ...     write("fail.py", ""
    ...     "fail = True\n"
    ...     "if fail:\n"
    ...     "    raise SystemExit('FAIL')\n"
    ...     "")

    >>> use_tmp_project()

Create a helper to validate parent run and step links. Step links
should resolve to their expected run directories.

    >>> def check_steps(link_names):
    ...     parent_dir = run_capture(f"guild select {len(link_names)+1} --dir")
    ...     for i, link_name in enumerate(link_names[::-1]):
    ...         step_run_dir = run_capture(f"guild select {i+1} --dir")
    ...         step_link_target = realpath(path(parent_dir, link_name))
    ...         assert step_link_target == step_run_dir, (parent_dir, link_name, i+1)

## Restart pipeline with errors

`m1:steps-restart` runs two steps, the second of which fails by
default.

    >>> run("guild run m1:steps-restart -y")
    INFO: [guild] running fail: m1:fail fail=no
    INFO: [guild] running fail: m1:fail fail=yes
    FAIL
    <exit 1>

    >>> run("guild runs -s")
    [1]  m1:fail           error      fail=yes
    [2]  m1:fail           completed  fail=no
    [3]  m1:steps-restart  error      fail=yes

    >>> run("guild ls -Fo steps-restart -n")
    fail/
    fail_2/

Confirm that the step links resolve to the expected step runs.

    >>> check_steps(["fail", "fail_2"])

Note the current time to confirm that Guild restarts the expected runs.

    >>> from datetime import datetime
    >>> before_restart = datetime.now().replace(microsecond=0)

Restart the parent run using an updated flag to cause the second step
to succeed.

    >>> parent_run = run_capture("guild select -Fo steps-restart")
    >>> run(f"guild run --restart {parent_run} fail=no -y")
    INFO: [guild] restarting fail: ... fail=no
    INFO: [guild] restarting fail: ... fail=no

    >>> run("guild runs -s")
    [1]  m1:fail           completed  fail=no
    [2]  m1:fail           completed  fail=no
    [3]  m1:steps-restart  completed  fail=no

    >>> run("guild ls -Fo steps-restart -n")
    fail/
    fail_2/

    >>> check_steps(["fail", "fail_2"])

When Guild restarts a run, it updates its `started` attribute. Confirm
that the runs have been restarted by filtering on started time.

    >>> run(f"guild runs -s --started 'after {before_restart}'")
    [1]  m1:fail           completed  fail=no
    [2]  m1:fail           completed  fail=no
    [3]  m1:steps-restart  completed  fail=no

    >>> run(f"guild runs -s --started 'before {before_restart}'")
    <exit 0>

## Restart pipeline with validation error on flag and broken link

Initialize the project and run pipeline where one step has an invalid
flag (this creates a broken link).

    >>> use_tmp_project()
    >>> run("guild run m1:steps-validation-error -y")
    INFO: [guild] running fail: m1:fail fail=no validation.error=yes
    guild: unsupported flag 'validation.error'
    Try 'guild run m1:fail --help-op' for a list of flags or use --force-flags to skip this check.
    <exit 1>

    >>> run("guild runs -s")
    [1]  m1:steps-validation-error  error  fail=yes

Fix the pipeline and run the steps again; everything passes.

    >>> write("guild.yml", """
    ... - model: m1
    ...   operations:
    ...     steps-restart:
    ...       flags:
    ...         fail: yes
    ...       steps:
    ...         - fail fail=no
    ...         - fail fail=${fail}
    ...     steps-validation-error:
    ...       flags:
    ...         fail: yes
    ...       steps:
    ...         - fail fail=no
    ...         - fail fail=${fail}
    ...     fail:
    ...       flags-import: all
    ... """)

    >>> parent_run = run_capture("guild select -Fo steps-validation-error")
    >>> run(f"guild run --restart {parent_run} fail=no -y")
    INFO: [guild] running fail: m1:fail fail=no
    INFO: [guild] running fail: m1:fail fail=no

    >>> run("guild runs -s")
    [1]  m1:fail                    completed  fail=no
    [2]  m1:fail                    completed  fail=no
    [3]  m1:steps-validation-error  completed  fail=no

## TODO

- Move `m1:steps-repeat` from sample guild file to temp project (don't
  put under a model - just top level op)

- ensure that restart doesn't pick up project source code changes

- ensure that --force-sourcecode to pipeline causes restarts to pick
  up source code changes :(

- delete a run step link -> should auto-recreate it as if new run

- delete a run step link and replace with a file or dir -> should error

- delete a step run, orphaning the link

- show use of batch (default and random)
