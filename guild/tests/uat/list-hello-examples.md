# List `hello` examples

List from the `examples/hello` directory:

    >>> cd("examples/hello")

    >>> run("guild runs -o hello")
    [1:...]   hello:from-flag                    ...  completed  message=yop
    [2:...]   hello:from-flag                    ...  completed  message=yop
    [3:...]   hello:from-flag+                   ...  completed
    [4:...]   hello:from-flag                    ...  completed  message=hola
    [5:...]   hello:from-flag                    ...  completed  message=hello
    [6:...]   hello:from-flag+                   ...  completed
    [7:...]   hello:from-file-output             ...  completed  file-output=...
    [8:...]   hello:from-file-output             ...  completed
    [9:...]   hello:from-file                    ...  completed  file=.../alt-msg
    [10:...]  hello:from-file                    ...  completed
    [11:...]  hello:from-flag                    ...  completed  message='Howdy Guild!'
    [12:...]  hello:from-flag                    ...  completed
    [13:...]  hello:default                      ...  completed
    [14:...]  gpkg.hello/hello:from-file-output  ...  completed  test-4
    [15:...]  gpkg.hello/hello:from-file         ...  completed  test-3
    [16:...]  gpkg.hello/hello:from-flag         ...  completed  test-2
    [17:...]  gpkg.hello/hello:default           ...  completed  test-1
    <exit 0>

List from the `examples` directory:

    >>> cd("examples")

    >>> run("guild runs -o hello")
    [1:...]   hello:from-flag (hello)            ...  completed  message=yop
    [2:...]   hello:from-flag (hello)            ...  completed  message=yop
    [3:...]   hello:from-flag+ (hello)           ...  completed
    [4:...]   hello:from-flag (hello)            ...  completed  message=hola
    [5:...]   hello:from-flag (hello)            ...  completed  message=hello
    [6:...]   hello:from-flag+ (hello)           ...  completed
    [7:...]   hello:from-file-output (hello)     ...  completed  file-output=...
    [8:...]   hello:from-file-output (hello)     ...  completed
    [9:...]   hello:from-file (hello)            ...  completed  file=.../alt-msg
    [10:...]  hello:from-file (hello)            ...  completed
    [11:...]  hello:from-flag (hello)            ...  completed  message='Howdy Guild!'
    [12:...]  hello:from-flag (hello)            ...  completed
    [13:...]  hello:default (hello)              ...  completed
    [14:...]  gpkg.hello/hello:from-file-output  ...  completed  test-4
    [15:...]  gpkg.hello/hello:from-file         ...  completed  test-3
    [16:...]  gpkg.hello/hello:from-flag         ...  completed  test-2
    [17:...]  gpkg.hello/hello:default           ...  completed  test-1
    <exit 0>
