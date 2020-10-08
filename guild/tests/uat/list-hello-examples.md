# List `hello` examples

List from the `examples/hello` directory:

    >>> cd(example("hello"))

    >>> run("guild runs -Fo hello")
    [1:...]   hello       ...  completed  msg=yop
    [2:...]   hello       ...  completed  msg=yop
    [3:...]   hello+      ...  completed
    [4:...]   hello       ...  completed  msg=hola
    [5:...]   hello       ...  completed  msg=hello
    [6:...]   hello+      ...  completed
    [7:...]   hello-op    ...  completed  op=...
    [8:...]   hello-op    ...  completed  op=...
    [9:...]   hello-file  ...  completed  file=.../alt-msg
    [10:...]  hello-file  ...  completed  file=hello.txt
    [11:...]  hello       ...  completed  msg='Howdy Guild!'
    [12:...]  hello       ...  completed  msg='Hello Guild!'
    <exit 0>

List from the `examples` directory:

    >>> cd(example(""))

    >>> run("guild runs -Fo hello")
    [1:...]   hello (hello)         ...  completed  msg=yop
    [2:...]   hello (hello)         ...  completed  msg=yop
    [3:...]   hello+ (hello)        ...  completed
    [4:...]   hello (hello)         ...  completed  msg=hola
    [5:...]   hello (hello)         ...  completed  msg=hello
    [6:...]   hello+ (hello)        ...  completed
    [7:...]   hello-op (hello)      ...  completed  op=...
    [8:...]   hello-op (hello)      ...  completed  op=...
    [9:...]   hello-file (hello)    ...  completed  file=.../alt-msg
    [10:...]  hello-file (hello)    ...  completed  file=hello.txt
    [11:...]  hello (hello)         ...  completed  msg='Howdy Guild!'
    [12:...]  hello (hello)         ...  completed  msg='Hello Guild!'
    <exit 0>
