# Run `hello` package examples

Default (using model ref):

    >>> run("guild run -y hello:default")
    Hello Guild!
    <exit 0>

Flag (using full package ref):

    >>> run("guild run -y hello/hello:from-flag")
    Hello Guild, from a flag!
    <exit 0>

From file:

    >>> run("guild run -y hello:from-file")
    Resolving 'msg-file' resource
    Hello Guild, from a required file!
    <exit 0>

From file output:

    >>> run("guild run -y hello/hello:from-file-output")
    Resolving 'file-output' resource
    Latest from-file output:
    Hello Guild, from a required file!
    <exit 0>

Here are our runs:

    >>> run("guild runs -m hello")
    [0:...]  hello/hello:from-file-output  ... ...  completed
    [1:...]  hello/hello:from-file         ... ...  completed
    [2:...]  hello/hello:from-flag         ... ...  completed
    [3:...]  hello/hello:default           ... ...  completed
    <exit 0>
