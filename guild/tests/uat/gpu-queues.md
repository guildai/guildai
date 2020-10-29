# GPU Queues

Queues can be started with a `gpus` flags to indicate that staged runs
that the queue starts should be run with the specified GPU spec.

For these tests we'll use the hello example.

    >>> cd(example("hello"))

And delete existing runs:

    >>> quiet("guild runs rm -y")

## General Behavior

Let's start a queue in the background with `gpus` set.

    >>> run("guild run -y queue gpus=1 poll-interval=1 -t q1 --background")
    queue:queue started in background as ... (pidfile ...)
    <exit 0>

Here's the run info for the queue:

    >>> run("guild runs info")
    id: ...
    operation: queue
    from: guildai
    status: running
    started: ...
    stopped:
    marked: no
    label: q1 gpus=1 poll-interval=1 run-once=no wait-for-running=no
    sourcecode_digest:
    vcs_commit:
    run_dir: ...
    command: ... -um guild.plugins.queue_main --gpus 1 --poll-interval 1
    exit_status:
    pid: ...
    tags:
      - q1
    flags:
      gpus: 1
      poll-interval: 1
      run-once: no
      wait-for-running: no
    scalars:
    <exit 0>

Note that `gpus` is `1`. This means that any staged runs that the
queue starts will be started with `--gpus 1` - provided they don't
otherwise specify their own value for this option.

Let's stage an operation without specifying `--gpus`.

    >>> run("guild run -y hello -l default-gpus --stage")
    hello staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

Wait for the run to be started and run:

    >>> sleep(5)

Output from the queue:

    >>> run("guild cat --output -Fo queue")
    INFO: [queue] ... Waiting for staged runs
    INFO: [queue] ... Starting staged run ...
    Masking available GPUs (CUDA_VISIBLE_DEVICES='1')
    Hello Guild!
    INFO: [queue] ... Waiting for staged runs
    <exit 0>

The runs:

    >>> run("guild runs")
    [1:...]  hello  ...  completed   default-gpus
    [2:...]  queue  ...  running     q1 gpus=1 poll-interval=1 run-once=no wait-for-running=no
    <exit 0>

Confirm that the run used the expected `gpus` option:

    >>> run("guild cat -p .guild/attrs/run_params")
    ???
    gpus: '1'
    ...

This should translate to `CUDA_VISIBLE_DEVICES` environment being set
as well:

    >>> run("guild runs info --env")
    id: ...
    environment:
      ...
      CUDA_VISIBLE_DEVICES: '1'
      ...

## Staged Runs with GPUs specs

If a staged operation specifies a `--gpus` value that matches the
queue, the queue will start the operation.

    >>> run("guild run hello --gpus 1 -l gpus-1 --stage -y")
    Masking available GPUs (CUDA_VISIBLE_DEVICES='1')
    hello staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

Wait for the staged run to be started and finish:

    >>> sleep(5)

List the runs:

    >>> run("guild runs")
    [1:...]  hello  ...  completed  gpus-1
    [2:...]  hello  ...  completed  default-gpus
    [3:...]  queue  ...  running    q1 gpus=1 poll-interval=1 run-once=no wait-for-running=no
    <exit 0>

If a staged run specifies a different GPU spec, the queue will refuse
to start it.

    >>> run("guild run hello --gpus 2 -l gpus-2 --stage -y")
    Masking available GPUs (CUDA_VISIBLE_DEVICES='2')
    hello staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

Give the queue enough time to start the run, if would start it (it
should not):

    >>> sleep(5)

Show runs:

    >>> run("guild runs")
    [1:...]  hello  ...  staged     gpus-2
    [2:...]  hello  ...  completed  gpus-1
    [3:...]  hello  ...  completed  default-gpus
    [4:...]  queue  ...  running    q1 gpus=1 poll-interval=1 run-once=no wait-for-running=no
    <exit 0>

Confirm that the queue refused to start the run for the right reason:

    >>> run("guild cat --output -l q1")
    ???
    INFO: [queue] ... Waiting for staged runs
    INFO: [queue] ... Ignorning staged run ... (GPU spec mismatch: run is 2, queue is 1)
    <exit 0>

We can start another queue, which is associated with GPU `2`, to start
the staged run.

    >>> run("guild run queue gpus=2 poll-interval=1 -t q2 --background -y")
    queue:queue started in background as ... (pidfile ...)
    <exit 0>

Wait for the staged run to start:

    >>> sleep(5)

Check output from the latest queue:

    >>> run("guild cat --output -Fl q2")
    INFO: [queue] ... Starting staged run ...
    Masking available GPUs (CUDA_VISIBLE_DEVICES='2')
    Hello Guild!
    INFO: [queue] ... Waiting for staged runs
    <exit 0>

Show runs:

    >>> run("guild runs")
    [1:...]  hello  ...  completed  gpus-2
    [2:...]  queue  ...  running    q2 gpus=2 poll-interval=1 run-once=no wait-for-running=no
    [3:...]  hello  ...  completed  gpus-1
    [4:...]  hello  ...  completed  default-gpus
    [5:...]  queue  ...  running    q1 gpus=1 poll-interval=1 run-once=no wait-for-running=no
    <exit 0>

Stop the queues:

    >>> run("guild stop -y")
    Stopping ... (pid ...)
    Stopping ... (pid ...)
    <exit 0>
