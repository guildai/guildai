# Run `hello` package examples

Default (using model ref):

    >>> run("guild run -y hello:default --label test-1")
    Hello Guild!
    <exit 0>

Flag (using full package ref):

    >>> run("guild run -y hello/hello:from-flag --label test-2")
    Hello Guild, from a flag!
    <exit 0>

From file:

    >>> run("guild run -y hello:from-file --label test-3")
    Resolving msg-file dependency
    Hello Guild, from a required file!
    <exit 0>

From file output:

    >>> run("guild run -y hello/hello:from-file-output --label test-4")
    Resolving file-output dependency
    Using output from run ... for file-output resource
    Latest from-file output:
    Hello Guild, from a required file!
    <exit 0>

Here are our runs:

    >>> run("guild runs -o hello")
    [0:...]  hello/hello:from-file-output  ... ...  completed  test-4
    [1:...]  hello/hello:from-file         ... ...  completed  test-3
    [2:...]  hello/hello:from-flag         ... ...  completed  test-2
    [3:...]  hello/hello:default           ... ...  completed  test-1
    <exit 0>
