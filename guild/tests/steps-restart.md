# Steps with --restart

These steps extend those defined in [`steps.md`](steps.md) to
demonstrate Guild's behavior when restarting a pipeline.

Pipelines are commonly restarted when one or more steps fail.

Create and use a helper to initiliaze a fresh temporary project.

    >>> def use_tmp_project():
    ...     use_project(mkdtemp())
    ...
    ...     write("guild.yml", """
    ... steps-restart:
    ...   flags:
    ...     fail: yes
    ...   steps:
    ...     - fail fail=no
    ...     - fail fail=${fail}
    ... steps-validation-error:
    ...   flags:
    ...     fail: yes
    ...   steps:
    ...     - fail fail=no validation.error=yes
    ...     - fail fail=${fail}
    ... steps-batch:
    ...   flags:
    ...     fail: yes
    ...   steps:
    ...     - fail fail=[no,no,no]
    ... steps-random-batch:
    ...   steps:
    ...     - train x=[-2.0:2.0] --max-trials 3
    ... fail:
    ...   flags-import: all
    ... train:
    ...   flags-import: all
    ... """)
    ...
    ...     write("fail.py", """
    ... fail = True
    ... if fail:
    ...     raise SystemExit('FAIL')
    ... """)
    ...
    ...     write("train.py", """
    ... import numpy as np
    ... noise = 0.1
    ... x = 0
    ... loss = (np.sin(5 * x) * (1 - np.tanh(x ** 2)) + np.random.randn() * noise)
    ... print(f'loss: {loss}')
    ... """)

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

`steps-restart` runs two steps, the second of which fails by
default.

    >>> run("guild run steps-restart -y")
    INFO: [guild] running fail: fail fail=no
    INFO: [guild] running fail: fail fail=yes
    FAIL
    <exit 1>

    >>> run("guild runs -s")
    [1]  fail           error      fail=yes
    [2]  fail           completed  fail=no
    [3]  steps-restart  error      fail=yes

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
    [1]  fail           completed  fail=no
    [2]  fail           completed  fail=no
    [3]  steps-restart  completed  fail=no

    >>> run("guild ls -Fo steps-restart -n")
    fail/
    fail_2/

    >>> check_steps(["fail", "fail_2"])

When Guild restarts a run, it updates its `started` attribute. Confirm
that the runs have been restarted by filtering on started time.

    >>> run(f"guild runs -s --started 'after {before_restart}'")
    [1]  fail           completed  fail=no
    [2]  fail           completed  fail=no
    [3]  steps-restart  completed  fail=no

    >>> run(f"guild runs -s --started 'before {before_restart}'")
    <exit 0>

## Restart pipeline with validation error on flag and broken link

Initialize the project and run pipeline where one step has an invalid
flag (this creates a broken link).

    >>> use_tmp_project()
    >>> run("guild run steps-validation-error -y")
    INFO: [guild] running fail: fail fail=no validation.error=yes
    guild: unsupported flag 'validation.error'
    Try 'guild run fail --help-op' for a list of flags or use --force-flags to skip this check.
    <exit 1>

    >>> run("guild runs -s")
    [1]  steps-validation-error  error  fail=yes

Fix the pipeline.

    >>> write("guild.yml", """
    ... steps-restart:
    ...   flags:
    ...     fail: yes
    ...   steps:
    ...     - fail fail=no
    ...     - fail fail=${fail}
    ... steps-validation-error:
    ...   flags:
    ...     fail: yes
    ...   steps:
    ...     - fail fail=no
    ...     - fail fail=${fail}
    ... fail:
    ...   flags-import: all
    ... """)

Run the steps again.

    >>> parent_run = run_capture("guild select -Fo steps-validation-error")
    >>> run(f"guild run --restart {parent_run} fail=no -y")
    INFO: [guild] running fail: fail fail=no
    INFO: [guild] running fail: fail fail=no

Verify that the steps passed.

    >>> run("guild runs -s")
    [1]  fail                    completed  fail=no
    [2]  fail                    completed  fail=no
    [3]  steps-validation-error  completed  fail=no

## Pipeline step's run link replaced with a non-link produces error

Initialize the project and run the pipeline.

    >>> use_tmp_project()
    >>> run("guild run steps-restart fail=no -y")
    INFO: [guild] running fail: fail fail=no
    INFO: [guild] running fail: fail fail=no

    >>> run("guild runs -s")
    [1]  fail           completed  fail=no
    [2]  fail           completed  fail=no
    [3]  steps-restart  completed  fail=no

Remove link to first step and replace it with a file.

    >>> parent_run = run_capture("guild select -Fo steps-restart")
    >>> parent_path = path(guild_home(), "runs", parent_run)
    >>> step_link = path(parent_path, "fail")

    >>> dir(parent_path)
    ['.guild', 'fail', 'fail_2']

    >>> rm(step_link)
    >>> dir(parent_path)
    ['.guild', 'fail_2']

    >>> write(step_link, "test")
    >>> dir(parent_path)
    ['.guild', 'fail', 'fail_2']

Restart the pipeline and observe the error.

    >>> run(f"guild run --restart {parent_run} fail=no -y")
    guild: unexpected step run link /tmp/guild-test-.../runs/.../fail: expected symlink
    <exit 1>

## Pipeline step run deleted, orphaning link

Initialize the project and run the pipeline.

    >>> use_tmp_project()
    >>> run("guild run steps-restart fail=no -y")
    INFO: [guild] running fail: fail fail=no
    INFO: [guild] running fail: fail fail=no

    >>> run("guild runs -s")
    [1]  fail           completed  fail=no
    [2]  fail           completed  fail=no
    [3]  steps-restart  completed  fail=no

Delete the step that the first link points to.

    >>> parent_run = run_capture("guild select -Fo steps-restart")
    >>> parent_path = path(guild_home(), "runs", parent_run)
    >>> step = realpath(path(parent_path, "fail"))

    >>> dir(parent_path)
    ['.guild', 'fail', 'fail_2']

    >>> rmdir(step)
    >>> dir(parent_path)
    ['.guild', 'fail', 'fail_2']

    >>> exists(path(parent_path, "fail"))
    False

    >>> dir(parent_path)
    ['.guild', 'fail', 'fail_2']

Restarting the pipeline reruns all steps.

    >>> run(f"guild run --restart {parent_run} fail=no -y")
    INFO: [guild] running fail: fail fail=no
    INFO: [guild] restarting fail: ... fail=no

    >>> run("guild runs -s")
    [1]  fail           completed  fail=no
    [2]  fail           completed  fail=no
    [3]  steps-restart  completed  fail=no

    >>> dir(parent_path)
    ['.guild', 'fail', 'fail_2']

## Pipeline with restarted batch step

Initialize the project and run the batch step pipeline.

    >>> use_tmp_project()
    >>> run("guild run steps-batch fail=no -y")
    INFO: [guild] running fail: fail fail=[no, no, no]
    INFO: [guild] Running trial ...: fail (fail=no)
    INFO: [guild] Running trial ...: fail (fail=no)
    INFO: [guild] Running trial ...: fail (fail=no)

    >>> run("guild runs -s")
    [1]  fail         completed  fail=no
    [2]  fail         completed  fail=no
    [3]  fail         completed  fail=no
    [4]  fail+        completed
    [5]  steps-batch  completed  fail=no

Restarting the pipeline reruns the batch and new trials are generated.

    >>> parent_run = run_capture("guild select -Fo steps-batch")

    >>> run(f"guild run --restart {parent_run} fail=no -y")
    INFO: [guild] restarting fail: ... fail=[no, no, no]
    INFO: [guild] Running trial ...: fail (fail=no)
    INFO: [guild] Running trial ...: fail (fail=no)
    INFO: [guild] Running trial ...: fail (fail=no)

    >>> run("guild runs -s")
    [1]  fail         completed  fail=no
    [2]  fail         completed  fail=no
    [3]  fail         completed  fail=no
    [4]  fail+        completed
    [5]  steps-batch  completed  fail=no
    [6]  fail         completed  fail=no
    [7]  fail         completed  fail=no
    [8]  fail         completed  fail=no

## Pipeline with restarted random batch step

Initialize the project and run the batch step pipeline.

    >>> use_tmp_project()
    >>> run("guild run steps-random-batch -y")
    INFO: [guild] running train: train --max-trials 3 x='[-2.0:2.0]'
    INFO: [guild] Running trial ...: train (noise=0.1, x=...)
    loss: ...
    INFO: [guild] Running trial ...: train (noise=0.1, x=...)
    loss: ...
    INFO: [guild] Running trial ...: train (noise=0.1, x=...)
    loss: ...

    >>> run("guild runs -s")
    [1]  train               completed  noise=0.1 x=...
    [2]  train               completed  noise=0.1 x=...
    [3]  train               completed  noise=0.1 x=...
    [4]  train+skopt:random  completed
    [5]  steps-random-batch  completed

Restarting the pipeline reruns the batch and new trials are generated.

    >>> parent_run = run_capture("guild select -Fo steps-random-batch")
    >>> run(f"guild run --restart {parent_run} -y")
    INFO: [guild] restarting train: ... --max-trials 3 x='[-2.0:2.0]'
    INFO: [guild] Running trial ...: train (noise=0.1, x=...)
    loss: ...
    INFO: [guild] Running trial ...: train (noise=0.1, x=...)
    loss: ...
    INFO: [guild] Running trial ...: train (noise=0.1, x=...)
    loss: ...

    >>> run("guild runs -s")
    [1]  train               completed  noise=0.1 x=...
    [2]  train               completed  noise=0.1 x=...
    [3]  train               completed  noise=0.1 x=...
    [4]  train+skopt:random  completed
    [5]  steps-random-batch  completed
    [6]  train               completed  noise=0.1 x=...
    [7]  train               completed  noise=0.1 x=...
    [8]  train               completed  noise=0.1 x=...

## TODO

- ensure that restart doesn't pick up project source code changes

- ensure that --force-sourcecode to pipeline causes restarts to pick
  up source code changes :(

- delete a run step link -> should auto-recreate it as if new run
