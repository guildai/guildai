# Remote stage and queue

Delete remote runs as baseline.

    >>> quiet("guild runs rm -y --remote guild-uat")

Start a queue with no-wait (detached):

    >>> run("guild run queue -y -r guild-uat --no-wait")
    Initializing remote run
    Starting queue:queue on guild-uat as ...
    ... is running on guild-uat
    To watch use 'guild watch ... -r guild-uat'
    <exit 0>

Current runs:

    >>> run("guild runs --remote guild-uat")
    [1:...]  queue  ...  running
    <exit 0>

Run some staged operations.

    >>> quiet("guild run -y -r guild-uat --stage gpkg.hello/hello:default")
    >>> cd("examples/hello")
    >>> quiet("guild run -y -r guild-uat --stage from-flag message=whoop")
    >>> quiet("guild run -y -r guild-uat --stage gpkg.hello/hello:from-file")

Wait to let runs finish.

    >>> sleep(10)

Show runs:

    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.hello/hello:from-file  ...  completed
    [2:...]  hello/hello:from-flag       ...  completed  message=whoop
    [3:...]  gpkg.hello/hello:default    ...  completed
    [4:...]  queue                       ...  running
    <exit 0>

Stop the queue:

    >>> run("guild stop -y -r guild-uat -o queue")
    Stopping ... (pid ...)
    <exit 0>

Show runs:

    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.hello/hello:from-file  ...  completed
    [2:...]  hello/hello:from-flag       ...  completed   message=whoop
    [3:...]  gpkg.hello/hello:default    ...  completed
    [4:...]  queue                       ...  terminated
    <exit 0>
