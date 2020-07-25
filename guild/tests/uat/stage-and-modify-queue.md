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
    <exit 0>

Write v2 of a script:

    >>> write("say.py", "print('Hello v2')")

Queue an operation for v2:

    >>> run("guild run say.py --stage -y")
    say.py staged as ...
    To start the operation, use 'guild run --start ...'
    <exit 0>

Run a queue once:

    >>> run("guild run queue run-once=yes -y")
    INFO: [queue] ... Starting staged run ...
    Hello v1
    INFO: [queue] ... Starting staged run ...
    Hello v2
    <exit 0>
