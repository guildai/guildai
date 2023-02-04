# Guild example: hello

    >>> cd(example("hello"))

List operations:

    >>> run("guild ops")
    hello       Say hello to my friends
    hello-file  Show a message from a file
    hello-op    Show a message from a hello-file operation
    <exit 0>

## `hello`

    >>> run("guild run hello -y")
    Hello Guild!
    <exit 0>

    >>> run("guild run hello msg=Whoop -y")
    Whoop
    <exit 0>

## `hello-file`

    >>> run("guild run hello-file -y")
    Resolving file
    Using hello.txt for file
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out
    <exit 0>

    >>> run("guild runs info --manifest")  # doctest: +REPORT_UDIFF
    id: ...
    operation: hello-file
    from: .../examples/hello/guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: file=hello.txt
    sourcecode_digest: ...
    vcs_commit: ...
    run_dir: ...
    command: ... -um guild.op_main cat -- --file hello.txt
    exit_status: 0
    pid:
    tags:
    flags:
      file: hello.txt
    scalars:
    manifest:
      dependencies:
        - hello.txt
      sourcecode:
        - README.md
        - cat.py
        - guild.yml
        - repeat.py
        - say.py
    <exit 0>

    >>> tmp = mkdtemp()
    >>> tmp_file = path(tmp, "hello")
    >>> write(tmp_file, "A temp file!")

    >>> run("guild run hello-file file=%s -y" % tmp_file)
    Resolving file
    Using .../hello for file
    Reading message from .../hello
    A temp file!
    Saving message to msg.out
    <exit 0>

## `hello-op`

    >>> run("guild run hello-op -y")
    Resolving op
    Using run ... for op
    Reading message from msg.out
    A temp file!
    <exit 0>

    >>> hello_op_run_id = run_capture("guild select -Fo hello-file 2")
    >>> run(f"guild run hello-op op={hello_op_run_id} -y")
    Resolving op
    Using run ... for op
    Reading message from msg.out
    Hello, from a file!
    <exit 0>
