# Hello examples

The `hello` example provides a simple model that prints messages for
it operations.

We'll run through the various operations in this test.

    >>> cd("examples/hello")

Delete runs for these tests.

    >>> quiet("guild runs rm -y")

## Models

    >>> run("guild models", ignore="Refreshing flags")
    hello  A "hello world" sample model
    <exit 0>

## Operations

    >>> run("guild operations")
    hello:default           Print a default message
    hello:from-file         Print a message from a file
    hello:from-file-output  Print output from last file-output operation
    hello:from-flag         Print a message
    <exit 0>

### `default`

The `default` operation simply prints a hard-coded message.

    >>> run("guild run default -y", ignore="RuntimeWarning")
    Hello Guild!
    <exit 0>

### `from-flag`

The `from-flag` operation prints a message defined by a flag.

Here's the default output:

    >>> run("guild run from-flag -y")
    Hello Guild, from a flag!
    <exit 0>

And the output when we provide a value for the message flag:

    >>> run("guild run from-flag message='Howdy Guild!' -y")
    Howdy Guild!
    <exit 0>

### `from-file`

The `from-file` operation prints a message contained in a file. By
default it will print the contents of a default file:

    >>> run("guild run from-file -y")
    Resolving msg-file dependency
    Hello Guild, from a required file!
    <exit 0>

Note that this file is specified as a required resource in the model.

We can provide an alternative.

    >>> quiet("echo 'Yo yo, what up Guild!' > $WORKSPACE/alt-msg")
    >>> run("guild run from-file file=$WORKSPACE/alt-msg -y")
    Resolving msg-file dependency
    Yo yo, what up Guild!
    <exit 0>

### `from-file-output`

When we run `from-file-output`, we get the latest output from
`from-file`:

    >>> run("guild run from-file-output -y")
    Resolving from-file-output dependency
    Using output from run ... for from-file-output resource
    Latest from-file output:
    Yo yo, what up Guild!
    <exit 0>

We can view the sources of all resolved dependencies for a run using
the `--deps` option of `guild runs info`:

    >>> run("guild runs info --deps")
    id: ...
    operation: hello:from-file-output
    from: .../guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label:
    sourcecode_digest: ...
    run_dir: ...
    command: ... -um guild.op_main say --file-output --
    exit_status: 0
    pid:
    flags:
      from-file-output: ...
    scalars:
    dependencies:
      from-file-output:
        - ../.../output
    <exit 0>

`file-output` as a flag.

Here's a preview of the command:

    >>> run("guild run from-file-output from-file-output=foobar", timeout=5)
    WARNING: cannot find a suitable run for required resource 'from-file-output'
    You are about to run hello:from-file-output
      from-file-output: foobar
    Continue? (Y/n)
    <exit ...>

We'll use the first run for `from-file`.

    >>> run("""
    ... run_id=`guild runs -o hello:from-file | grep 'from-file ' | tail -n1 | cut -d: -f2 | cut -b 1-8`
    ... echo "from-file run: $run_id"
    ... guild run from-file-output from-file-output=$run_id -y
    ... """)
    from-file run: ...
    Resolving from-file-output dependency
    Using output from run ... for from-file-output resource
    Latest from-file output:
    Hello Guild, from a required file!
    <exit 0>

### Run a batch

    >>> run("guild run from-flag message=[hello,hola] -y")
    INFO: [guild] Running trial ...: hello:from-flag (message=hello)
    hello
    INFO: [guild] Running trial ...: hello:from-flag (message=hola)
    hola
    <exit 0>

### Run a batch using list concatenation

    >>> run("guild run from-flag message=[yop]*2 -y")
    INFO: [guild] Running trial ...: hello:from-flag (message=yop)
    yop
    INFO: [guild] Running trial ...: hello:from-flag (message=yop)
    yop
    <exit 0>
