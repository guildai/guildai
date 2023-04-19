# Steps with --restart

These steps extend those defined in [`steps.md`](steps.md) to
demonstrate Guild's behavior when restarting a pipeline.

Pipelines are commonly restarted when one or more steps fail.

The tests below modify project source code and so use an ephemeral
project rather than a test sample.

    >>> def use_tmp_project():
    ...     project_dir = mkdtemp()
    ...     copytree(sample("projects", "steps-restart"), project_dir)
    ...     use_project(project_dir)

    >>> use_tmp_project()

Create a helper to validate parent run and step links. Step links
should resolve to their expected run directories.

    >>> def check_steps(link_names):
    ...     parent_dir = run_capture(f"guild select {len(link_names)+1} --dir")
    ...     for i, link_name in enumerate(link_names[::-1]):
    ...         step_run_dir = run_capture(f"guild select {i+1} --dir")
    ...         step_link_target = realpath(path(parent_dir, link_name))
    ...         assert step_link_target == step_run_dir, (parent_dir, link_name, i+1)

Import `datetime` for filtering runs by when they were ran.

    >>> from datetime import datetime

## Restart pipeline with errors

`steps-restart` runs two steps, the second of which fails by default.

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

Note the current time to confirm that Guild restarts the expected
runs.

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

## Step pre-run validation errors

When prepraring to run a step, `steps_main` creates a link to a
non-existing run directory. This ensures that it can detect a run that
was not started, e.g. due to a validation error.

The `steps-validation-error` operation is a pipeline that runs a step
with an invalid flag value.

Reset the project.

    >>> use_tmp_project()

Run the pipeline with the default values. The step is run but fails
with a flag validation error. This occurs before the step run is
created.

    >>> run("guild run steps-validation-error -y")
    INFO: [guild] running train: train x=foo
    guild: invalid value foo for x: invalid value for type 'number'
    <exit 1>

Show the runs. There is only a `steps-validation-error` run (the
pipeline) - the step run was not created.

    >>> run("guild runs -s")
    [1]  steps-validation-error  error  x=foo

The pipeline run has a link to an non-existing run directory.

    >>> run("guild ls -n")
    train

The link target does not exist.

    >>> train_step_link = run_capture("guild ls -f -p train")

    >>> islink(train_step_link)
    True

    >>> exists(train_step_link)
    False

Restart the pipeline with a valid flag value for `x`.

    >>> parent_run = run_capture("guild select")

    >>> run(f"guild run --restart {parent_run} x=1 -y")
    INFO: [guild] running train: train x=1
    loss: ...

The step run is completed.

    >>> run("guild runs -s")
    [1]  train                   completed  noise=0.1 x=1
    [2]  steps-validation-error  completed  x=1

Verify that the step link resolves as expected.

    >>> check_steps(["train"])

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
    guild: unexpected step run link .../guild-test-.../runs/.../fail: expected symlink
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

## Pipeline restart uses latest source code with --force-sourcecode

Initialize the project and run the pipeline.

    >>> use_tmp_project()
    >>> run("guild run steps-force-sourcecode -y")
    INFO: [guild] running simple.py: simple.py
    hello

Change the sourcecode.

    >>> write("simple.py", """
    ... print('bye')
    ... """)

Rerun the pipeline with `--force-sourcecode` and new output is generated.

    >>> parent_run = run_capture("guild select -Fo steps-force-sourcecode")
    >>> run(f"guild run --restart {parent_run} --force-sourcecode  -y")
    INFO: [guild] restarting simple.py: ... --force-sourcecode
    bye

## Pipeline restart doesn't pick up source code changes

Initialize the project and run the pipeline.

    >>> use_tmp_project()
    >>> run("guild run steps-force-sourcecode -y")
    INFO: [guild] running simple.py: simple.py
    hello

Change the sourcecode.

    >>> write("simple.py", """
    ... print('bye')
    ... """)

Rerun the pipeline without `--force-sourcecode` and old output is generated.

    >>> parent_run = run_capture("guild select -Fo steps-force-sourcecode")
    >>> run(f"guild run --restart {parent_run}  -y")
    INFO: [guild] restarting simple.py: ...
    hello

## (bug) Pipeline with batch step picks up sourcecode changes on restart

Initialize the project and run the pipeline.

    >>> use_tmp_project()
    >>> run("guild run steps-random-batch -y")
    INFO: [guild] running train: train --max-trials 3 x='[-2.0:2.0]'
    INFO: [guild] Running trial ...: train (noise=0.1, x=...)
    loss: ...
    INFO: [guild] Running trial ...: train (noise=0.1, x=...)
    loss: ...
    INFO: [guild] Running trial ...: train (noise=0.1, x=...)
    loss: ...

Add a new flag to the `train.py` script.

    >>> write("train.py", """
    ... import numpy as np
    ... noise = 0.1
    ... x = 0
    ... y = 0
    ... loss = (np.sin(5 * x) * (1 - np.tanh(x ** 2)) + np.random.randn() * noise)
    ... print(f'moss: moss')
    ... print(f'loss: {loss}')
    ... """)

Rerun the pipeline without `--force-sourcecode` and new flag is wrongly shown.

    >>> parent_run = run_capture("guild select -Fo steps-random-batch")
    >>> run(f"guild run --restart {parent_run} -y")
    INFO: [guild] restarting train: ... --max-trials 3 x='[-2.0:2.0]'
    INFO: [guild] Running trial ...: train (noise=0.1, x=..., y=0)
    loss: ...
    INFO: [guild] Running trial ...: train (noise=0.1, x=..., y=0)
    loss: ...
    INFO: [guild] Running trial ...: train (noise=0.1, x=..., y=0)
    loss: ...

## Deleted pipeline step link causes lost reference and new step run

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
    >>> orphan_run = realpath(step_link)

    >>> dir(parent_path)
    ['.guild', 'fail', 'fail_2']

    >>> rm(step_link)
    >>> dir(parent_path)
    ['.guild', 'fail_2']

Restart the pipeline and observe the error.

    >>> run(f"guild run --restart {parent_run} fail=no -y")
    INFO: [guild] running fail: fail fail=no
    INFO: [guild] restarting fail: ... fail=no

Note that the new run link exists and its target is different from the old one.

    >>> run("guild runs -s")
    [1]  fail           completed  fail=no
    [2]  fail           completed  fail=no
    [3]  steps-restart  completed  fail=no
    [4]  fail           completed  fail=no

    >>> dir(parent_path)
    ['.guild', 'fail', 'fail_2']

    >>> new_step = realpath(path(parent_path, "fail"))
    >>> new_step == orphan_run
    False

And the old run still exists.

    >>> exists(orphan_run)
    True

## Restart pipeline with --needed flag

`steps-restart` runs two steps, the second of which fails by default.

    >>> use_tmp_project()
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

Note the current time to confirm that Guild restarts the expected
runs.

    >>> before_restart = datetime.now().replace(microsecond=0)

Restart the parent run using an updated flag to cause the second step
to succeed, along with the `--needed` flag to only run failing steps.

    >>> parent_run = run_capture("guild select -Fo steps-restart")

    >>> run(f"guild run --restart {parent_run} --needed fail=no -y")
    INFO: [guild] restarting fail: ... --needed fail=no
    Skipping run because flags have not changed (--needed specified)
    INFO: [guild] restarting fail: ... fail=no

    >>> run("guild runs -s")
    [1]  fail           completed  fail=no
    [2]  steps-restart  completed  fail=no
    [3]  fail           completed  fail=no

After restarting there are still only two links to the two step runs.

    >>> run("guild ls -Fo steps-restart -n")
    fail/
    fail_2/

When Guild restarts a run, it updates its `started` attribute. Confirm
that the runs have been restarted by filtering on started time.

    >>> run(f"guild runs -s --started 'after {before_restart}'")
    [1]  fail           completed  fail=no
    [2]  steps-restart  completed  fail=no

    >>> run(f"guild runs -s --started 'before {before_restart}'")
    [1]  fail           completed  fail=no
