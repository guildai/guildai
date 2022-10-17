# Additional dependency

Additional deps can be specified for the `run` command as '-D' or
'--dep' arguments.

    >>> project = Project(sample("projects", "additional-deps"))

When running `op.py` directly, the required file `file1` is not
available in the run directory.

    >>> project.run("op.py")
    Traceback (most recent call last):
    ...
    FileNotFoundError: [Errno 2] No such file or directory: 'file1'
    <exit 1>

We can provide this file as an additional dependency.

    >>> project.run("op.py", deps=("file1",))
    Resolving file1
    Hello from file1
