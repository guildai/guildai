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
    [1:...]  queue  ...  running  poll-interval=10 run-once=no wait-for-running=no
    <exit 0>

Run some staged operations.

    >>> quiet("guild run -y -r guild-uat --stage gpkg.hello/hello:default")
    >>> quiet("guild -C %s run -y -r guild-uat --stage hello msg=whoop"
    ...       % example("hello-package"))
    >>> quiet("guild run -y -r guild-uat --stage gpkg.hello/hello:from-file")

Wait to let runs finish.

    >>> sleep(10)

Show runs:

    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.hello/hello:from-file  ...  completed  file=msg.txt
    [2:...]  gpkg.hello/hello            ...  completed  msg=whoop
    [3:...]  gpkg.hello/hello:default    ...  completed
    [4:...]  queue                       ...  running    poll-interval=10 run-once=no wait-for-running=no
    <exit 0>

Stop the queue:

    >>> run("guild stop -y -r guild-uat -Fo queue")
    Stopping ... (pid ...)
    <exit 0>

Show runs:

    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.hello/hello:from-file  ...  completed   file=msg.txt
    [2:...]  gpkg.hello/hello            ...  completed   msg=whoop
    [3:...]  gpkg.hello/hello:default    ...  completed
    [4:...]  queue                       ...  terminated  poll-interval=10 run-once=no wait-for-running=no
    <exit 0>
