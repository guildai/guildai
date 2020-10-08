# Hello examples

The `hello` example provides a simple model that prints messages for
it operations.

We'll run through the various operations in this test.

    >>> cd(example("hello"))

Delete runs for these tests.

    >>> quiet("guild runs rm -y")

## Models

The `hello` uses operation-only format.

    >>> run("guild models")
    <exit 0>

## Operations

    >>> run("guild operations")
    hello       Say hello to my friends
    hello-file  Show a message from a file
    hello-op    Show a message from a hello-file operation
    <exit 0>

### `hello`

The `hello` operation prints a message defined by a flag.

Here's the default output:

    >>> run("guild run hello -y")
    Hello Guild!
    <exit 0>

And the output when we provide a value for the message flag:

    >>> run("guild run hello msg='Howdy Guild!' -y")
    Howdy Guild!
    <exit 0>

### `hello-file`

The `hello-file` operation prints a message contained in a file. By
default it will print the contents of a default file:

    >>> run("guild run hello-file -y")
    Resolving file dependency
    Using hello.txt for file resource
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out
    <exit 0>

We can provide an alternative file.

    >>> quiet("echo 'Yo yo, what up Guild!' > $WORKSPACE/alt-msg")
    >>> run("guild run hello-file file=$WORKSPACE/alt-msg -y")
    Resolving file dependency
    Using .../alt-msg for file resource
    Reading message from .../alt-msg
    Yo yo, what up Guild!
    <BLANKLINE>
    Saving message to msg.out
    <exit 0>

### `hello-op`

When we run `hello-op`, we get the latest output from `hello-file`:

    >>> run("guild run hello-op -y")
    Resolving op dependency
    Using run ... for op resource
    Reading message from msg.out
    Yo yo, what up Guild!
    <exit 0>

We can view the sources of all resolved dependencies for a run using
the `--deps` option of `guild runs info`:

    >>> run("guild runs info --deps")
    id: ...
    operation: hello-op
    from: .../guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: op=...
    sourcecode_digest: ...
    vcs_commit: ...
    run_dir: ...
    command: ... -um guild.op_main cat --
    exit_status: 0
    pid:
    tags:
    flags:
      op: ...
    scalars:
    dependencies:
      op:
        op:
          config: ...
          paths:
          - ../.../msg.out
          uri: operation:hello-file
    <exit 0>

Here's a preview of the command:

    >>> run("guild run hello-op op=foobar", timeout=5)
    WARNING: cannot find a suitable run for required resource 'op'
    You are about to run hello-op
      op: foobar
    Continue? (Y/n)
    <exit ...>

Let's use the first run for `hello-file`, rather than the latest.

    >>> run("guild run hello-op op=`guild select -Fo hello-file 2` -y")
    Resolving op dependency
    Using run ... for op resource
    Reading message from msg.out
    Hello, from a file!
    <exit 0>

### Run a batch

    >>> run("guild run hello msg=[hello,hola] -y")
    INFO: [guild] Running trial ...: hello (msg=hello)
    hello
    INFO: [guild] Running trial ...: hello (msg=hola)
    hola
    <exit 0>

### Run a batch using list concatenation

    >>> run("guild run hello msg=[yop]*2 -y")
    INFO: [guild] Running trial ...: hello (msg=yop)
    yop
    INFO: [guild] Running trial ...: hello (msg=yop)
    yop
    <exit 0>
