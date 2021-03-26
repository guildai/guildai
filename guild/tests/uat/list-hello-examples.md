# List `hello` examples

List from the `examples/hello` directory:

    >>> cd(example("hello"))

    >>> run("guild runs -Fo 'hello*'")
    [1:...]   hello       ...  completed  msg=yop
    [2:...]   hello       ...  completed  msg=yop
    [3:...]   hello       ...  completed  msg=hola
    [4:...]   hello       ...  completed  msg=hello
    [5:...]   hello-op    ...  completed  op=...
    [6:...]   hello-op    ...  completed  op=...
    [7:...]   hello-file  ...  completed  file=.../alt-msg
    [8:...]   hello-file  ...  completed  file=hello.txt
    [9:...]   hello       ...  completed  msg='Howdy Guild!'
    [10:...]  hello       ...  completed  msg='Hello Guild!'
    <exit 0>

List from the `examples` directory:

    >>> cd(example(""))

    >>> run("guild runs -Fo 'hello*'")
    [1:...]   hello (hello)         ...  completed  msg=yop
    [2:...]   hello (hello)         ...  completed  msg=yop
    [3:...]   hello (hello)         ...  completed  msg=hola
    [4:...]   hello (hello)         ...  completed  msg=hello
    [5:...]   hello-op (hello)      ...  completed  op=...
    [6:...]   hello-op (hello)      ...  completed  op=...
    [7:...]   hello-file (hello)    ...  completed  file=.../alt-msg
    [8:...]   hello-file (hello)    ...  completed  file=hello.txt
    [9:...]   hello (hello)         ...  completed  msg='Howdy Guild!'
    [10:...]  hello (hello)         ...  completed  msg='Hello Guild!'
    <exit 0>
