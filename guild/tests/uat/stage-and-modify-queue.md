# Stage and modify queue

These tests verify that a queue runs the souce code from the staged
run and not from the original project.

It supports this workflow:

- Stage a run with source code v1
- Modify source code to be v2
- Stage a run with source code v2
- Run the queue once

Create a project with a script that prints a message.

    >>> project = mkdtemp()
    >>> cd(project)

Write v1 of a script:

    >>> write("say.py", "print('Hello v1')")

Queue an operation for v1:

    >>> run("guild run say.py --stage -y")
    say.py staged as ...
    To start the operation, use 'guild run --start ...'

Write v2 of a script:

    >>> write("say.py", "print('Hello v2')")

Queue an operation for v2:

    >>> run("guild run say.py --stage -y")
    say.py staged as ...
    To start the operation, use 'guild run --start ...'

Run a queue once:

    >>> run("guild run queue run-once=yes --keep-run -y")
    INFO: [guild] ... Starting queue
    INFO: [guild] ... Starting staged run ...
    Hello v1
    INFO: [guild] ... Starting staged run ...
    Hello v2
    INFO: [guild] ... Stopping queue

    >>> run("guild runs -s -n3")
    [1]  say.py  completed
    [2]  say.py  completed
    [3]  queue   completed  poll-interval=10 run-once=yes wait-for-running=no
