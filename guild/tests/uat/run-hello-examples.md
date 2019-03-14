# Hello examples

The `hello` example provides a simple model that prints messages for
it operations.

We'll run through the various operations in this test.

    >>> cd("examples/hello")

## Models

    >>> run("guild models -p .", ignore="Refreshing project")
    hello  A "hello world" sample model
    <exit 0>

## Operations

    >>> run("guild operations -p .")
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

Guild captures project source, which we can list using `runs info`:

    >>> run("guild runs info --source")
    id: ...
    operation: hello:from-flag
    status: completed
    started: ...
    stopped: ...
    marked: no
    label:
    run_dir: ...
    command: ... -um guild.op_main say --message "Howdy Guild!"
    exit_status: 0
    pid:
    flags:
      message: Howdy Guild!
    source:
      Makefile
      guild.yml
      msg.txt
      say.py
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
    Resolving file-output dependency
    Using output from run ... for file-output resource
    Latest from-file output:
    Yo yo, what up Guild!
    <exit 0>

We can view the sources of all resolved dependencies for a run using
the `--deps` option of `guild runs info`:

    >>> run("guild runs info --deps")
    id: ...
    operation: hello:from-file-output
    status: completed
    ...
    dependencies:
      file-output:
        .../runs/.../output
    <exit 0>

We can specify an alternative run for `from-file-output` by specifying
`file-output` as a flag.

Here's a preview of the command:

    >>> run("guild run from-file-output file-output=foobar", timeout=1)
    You are about to run hello:from-file-output
      file-output: foobar
    Continue? (Y/n)
    <exit ...>

We'll use the first run for `from-file`.

    >>> run("""
    ... run_id=`guild runs -o hello:from-file | grep 'from-file ' | tail -n1 | cut -d: -f2 | cut -b 1-8`
    ... guild run from-file-output file-output=$run_id -y
    ... """)
    Resolving file-output dependency
    Using output from run ... for file-output resource
    Latest from-file output:
    Hello Guild, from a required file!
    <exit 0>
