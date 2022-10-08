---
doctest-type: bash
---

# Tests - Erlang Plugin

The example Erlang plugin is a simple example of a Guild AI plugin.

The plugin requires Erlang.

    $ which escript
    ???/escript

We can run `hello.erl` directly as an operation.

    $ guild run samples/hello.erl --help-op
    Usage: guild run [OPTIONS] hello.erl [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      who  (default is Joe)


    $ guild run samples/hello.erl -y
    Hello Joe!

    $ guild run samples/hello.erl who=Guild -y
    Hello Guild!

    $ guild runs -n2
    [1:...]  hello.erl (samples)  ...  completed  who=Guild
    [2:...]  hello.erl (samples)  ...  completed  who=Joe
