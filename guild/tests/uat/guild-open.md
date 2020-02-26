# Guild open cmd

Guild `open` is used to open a run file or directory.

Generate a single hello example run to test:

    >>> cd(example("hello"))

    >>> run("guild run -y")
    Hello Guild!
    <exit 0>

    >>> run("guild runs -n1")
    [1:...]  hello  ...  completed  msg='Hello Guild!'
    <exit 0>

Various uses of `open` with the `echo` command to show how arguments
are passed through:

    >>> run("guild open -c echo")
    ???/
    <exit 0>

    >>> run("guild open -c 'echo a b c'")
    a b c .../
    <exit 0>

    >>> run("guild open -c 'echo a b c' -p foo.txt")
    a b c .../foo.txt
    <exit 0>
