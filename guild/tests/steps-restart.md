# Steps with --restart

These steps extend those defined in [`steps.md`](steps.md) to
demonstrate Guild's behavior when restarting a pipeline.

Pipelines are commonly restarted when one or more steps fail.

Use the sample project `steps` to illustrate the behavior.

    >>> use_project("steps")

Create a helper to validate parent run and step links. Step links
should resolve to their expected run directories.

    >>> def check_steps(parent_spec, link_names, step_specs):
    ...     parent_dir = run_capture(f"guild select {parent_spec} --dir")
    ...     for link_name, step_spec in zip(link_names, step_specs):
    ...         step_run_dir = run_capture(f"guild select {step_spec} --dir")
    ...         step_link_target = realpath(path(parent_dir, link_name))
    ...         assert step_link_target == step_run_dir, (parent_dir, link_name, step_spec)

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

    >>> check_steps("3", ["fail", "fail_2"], ["2", "1"])

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

    >>> check_steps("3", ["fail", "fail_2"], ["2", "1"])

When Guild restarts a run, it updates its `started` attribute. Confirm
that the runs have been restarted by filtering on started time.

    >>> run(f"guild runs -s --started 'after {before_restart}'")
    [1]  m1:fail           completed  fail=no
    [2]  m1:fail           completed  fail=no
    [3]  m1:steps-restart  completed  fail=no

    >>> run(f"guild runs -s --started 'before {before_restart}'")
    <exit 0>


## TODO

- `project_dir = mkdtemp()` insted of `use_project()`
- Move `fail.py` from steps sample project into tmp project (update
  `steps.md` to not include `fail.py` in examples)
  - Move `m1:steps-repeat` from sample guild file to temp project (don't
  put under a model - just top level op)
- ensure that restart doesn't pick up project source code changes
- ensure that --force-sourcecode to pipeline causes restarts to pick
  up source code changes :(
- step run doesn't start - e.g. validation error on flag
- delete a run step link -> should auto-recreate it as if new run
- delete a run step link and replace with a file or dir -> should error
- delete a step run, orphaning the link
- show use of batch (default and random)

Example of using temp dir for test-defined project:

    >>> use_project(mkdtemp())

    >>> write("guild.yml", """
    ... # Sample guild file!
    ... """)

Etc.
