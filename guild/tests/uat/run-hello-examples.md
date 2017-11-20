# Hello examples

The `hello` example provides a simple model that prints messages for
it operations.

We'll run through the various operations in this test.

    >>> cd("examples/hello")

## Models

    >>> run("guild models")
    Limiting models to the current directory (use --all to include all)
    ./hello  A "hello world" sample model
    <exit 0>

## Operations

    >>> run("guild operations")
    Limiting models to the current directory (use --all to include all)
    ./hello:default           Print a default message
    ./hello:from-file         Print a message from a file
    ./hello:from-file-output  Print output from last file-output operation
    ./hello:from-flag         Print a message
    <exit 0>

### `default`

The `default` operation simply prints a hard-coded message.

    >>> run("guild run default -y")
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

### `from-file-output` part 1

The `from-file-output` operation requires output from the `from-file`
operation. When we try to run it without first having a completed run
for `from-file` we get an error.

    >>> run("guild run from-file-output -y")
    Resolving file-output resource
    guild: run failed because a dependency was not met: could not resolve
    'operation:from-file//output' in file-output resource: no suitable
    run for ./hello:from-file
    <exit 1>

### `from-file`

The `from-file` operation prints a message contained in a file. By
default it will print the contents of a default file:

    >>> run("guild run from-file -y")
    Resolving msg-file resource
    Hello Guild, from a required file!
    <exit 0>

Note that this file is specified as a required resource in the model.

We can provide an alternative.

    >>> quiet("echo 'Yo yo, what up Guild!' > $WORKSPACE/alt-msg")
    >>> run("guild run from-file file=$WORKSPACE/alt-msg -y")
    Resolving msg-file resource
    Yo yo, what up Guild!
    <exit 0>

### `from-file-output` part 2

Now that we have a successful run of `from-file` we can run
`from-from-output`:

    >>> run("guild run from-file-output -y")
    Resolving file-output resource
    Latest from-file output:
    Yo yo, what up Guild!
    <exit 0>
