---
doctest-type: bash
---

# Tests - Erlang Plugin

The example Erlang plugin is a simple example of a Guild AI plugin.

The plugin requires Erlang.

    $ which escript
    ???/escript

We can run `hello.erl` directly as an operation.

Use `--help-op` with the `run` command to show help for the operation.

    $ guild run samples/hello.erl --help-op
    Usage: guild run [OPTIONS] hello.erl [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      who  (default is Joe)

Use `--print-cmd` to show the underlying command that the plugin
generates for running the operation.

    $ guild run samples/hello --print-cmd

Run the operation with default flag values. These are defined in the
script using a configuration block. Note that this scheme only applies
to this example plugin --- it does not apply to other languages.

    $ guild run samples/hello.erl -y
    Hello Joe!

Specify a different value for `who`.

    $ guild run samples/hello.erl who=Guild -y
    Hello Guild!

List the two generated runs.

    $ guild runs -n2
    [1:...]  hello.erl (samples)  ...  completed  who=Guild
    [2:...]  hello.erl (samples)  ...  completed  who=Joe
