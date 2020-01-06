# Copy source code warnings

By default, Guild guards against copying too many source code files or
copying very large source code files.

## Max source code file count

Guild will not copy more than `op_util.MAX_DEFAULT_SOURCECODE_COUNT`
source code files by default.

    >>> from guild import op_util
    >>> op_util.MAX_DEFAULT_SOURCECODE_COUNT
    100

Let's illustrate by running an operation within a directory that
contains both a large number of text files.

    >>> project_dir = mkdtemp()
    >>> for i in range(op_util.MAX_DEFAULT_SOURCECODE_COUNT + 10):
    ...     touch(path(project_dir, "%0.3i.txt" % (i + 1)))

Here are our 110 files:

    >>> sourcecode_src = findl(project_dir)
    >>> len(sourcecode_src)
    110
    >>> for s in sourcecode_src:
    ...     print(s)
    001.txt
    002.txt
    ...
    109.txt
    110.txt

Here's a no-op script that we can run to test an operation:

    >>> touch(path(project_dir, "no_op.py"))

Let's run the no-op script using a project:

    >>> project = Project(project_dir)
    >>> run, out = project.run_capture(
    ...     "no_op.py",
    ...     extra_env={"PYTHONPATH": project_dir})
    >>> print(out)
    WARNING: Found more than 100 source code files but will only
    copy 100 as a safety measure. To control which files are copied,
    define 'sourcecode' for the operation in a Guild file.

Let's confirm that Guild only copied the first
`op_util.MAX_DEFAULT_SOURCECODE_COUNT` source code files.

    >>> sourcecode_copied = project.ls(run, sourcecode=True)
    >>> len(sourcecode_copied)
    100
    >>> for s in sourcecode_copied:
    ...     print(s)
    .guild/sourcecode/001.txt
    .guild/sourcecode/002.txt
    ...
    .guild/sourcecode/099.txt
    .guild/sourcecode/100.txt

We can override this behavior with explicit Guild file config.

    >>> cfg = """
    ... no_op.py:
    ...   sourcecode: '*.txt'
    ... """
    >>> write(path(project_dir, "guild.yml"), cfg)

Let's run the operation again:

    >>> run, _out = project.run_capture(
    ...     "no_op.py",
    ...     extra_env={"PYTHONPATH": project_dir})

And get the list of copied soure code files:

    >>> sourcecode_copied = project.ls(run, sourcecode=True)
    >>> len(sourcecode_copied)
    110
    >>> for s in sourcecode_copied:
    ...     print(s)
    .guild/sourcecode/001.txt
    .guild/sourcecode/002.txt
    ...
    .guild/sourcecode/109.txt
    .guild/sourcecode/110.txt

## Max source code file size

Guild also guards against copying souce code files that are too big.

The max file size is defined by
`op_util.MAX_DEFAULT_SOURCECODE_FILE_SIZE`.

    >>> op_util.MAX_DEFAULT_SOURCECODE_FILE_SIZE
    1048576

Let's create a new project with various files:

    >>> project_dir = mkdtemp()

A file that is one byte too big:

    >>> write(path(project_dir, "too-big.txt"),
    ...       "0" * (op_util.MAX_DEFAULT_SOURCECODE_FILE_SIZE + 1))

A file that is exactly at the max size:

    >>> write(path(project_dir, "max.txt"),
    ...       "0" * op_util.MAX_DEFAULT_SOURCECODE_FILE_SIZE)

An empty file:

    >>> touch(path(project_dir, "empty.txt"))

Here's our no-op script again:

    >>> touch(path(project_dir, "no_op.py"))

Here are the project files:

    >>> find(project_dir)
    empty.txt
    max.txt
    no_op.py
    too-big.txt

Let's run an operation with the default source code settings.

    >>> project = Project(project_dir)
    >>> run, out = project.run_capture("no_op.py")
    >>> print(out)
    WARNING: Skipping potential source code file ./too-big.txt
    because it's too big. To control which files are copied,
    define 'sourcecode' for the operation in a Guild file.

Here are our run source files:

    >>> for s in project.ls(run, sourcecode=True):
    ...     print(s)
    .guild/sourcecode/empty.txt
    .guild/sourcecode/max.txt
    .guild/sourcecode/no_op.py

Let's now provide config to override this behavior. In this case, we
extend the file select logic to include any `*.txt` file.

    >>> cfg = """
    ... no_op.py:
    ...   sourcecode:
    ...     - include: '*.txt'
    ... """
    >>> write(path(project_dir, "guild.yml"), cfg)

Run again with our new config:

    >>> run, _out = project.run_capture("no_op.py")

And the run source code:

    >>> for s in project.ls(run, sourcecode=True):
    ...     print(s)
    .guild/sourcecode/empty.txt
    .guild/sourcecode/guild.yml
    .guild/sourcecode/max.txt
    .guild/sourcecode/no_op.py
    .guild/sourcecode/too-big.txt

## Guarding against both file count and max size

Let's confirm that Guild guards against both conditions occurring in
the same project.

Create max number of files:

    >>> project_dir = mkdtemp()

    >>> for i in range(op_util.MAX_DEFAULT_SOURCECODE_COUNT):
    ...     touch(path(project_dir, "%0.3i.txt" % (i + 1)))

Next create a large file:

    >>> write(path(project_dir, "big.txt"),
    ...       "0" * (op_util.MAX_DEFAULT_SOURCECODE_FILE_SIZE + 1))

Our no_op operation:

    >>> touch(path(project_dir, "no_op.py"))

And a run:

    >>> project = Project(project_dir)
    >>> run, out = project.run_capture(
    ...     "no_op.py",
    ...     extra_env={"PYTHONPATH": project_dir})
    >>> print(out)
    WARNING: Found more than 100 source code files but will only
    copy 100 as a safety measure. To control which files are copied,
    define 'sourcecode' for the operation in a Guild file.

The run source code:

    >>> for s in project.ls(run, sourcecode=True):
    ...     print(s)
    .guild/sourcecode/001.txt
    .guild/sourcecode/002.txt
    ...
    .guild/sourcecode/099.txt
    .guild/sourcecode/100.txt
