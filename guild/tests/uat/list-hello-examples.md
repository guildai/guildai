# List `hello` examples

List from the `examples/hello` directory:

    >>> cd("examples/hello")

    >>> run("guild runs -o hello")
    [1:...]   hello:from-flag                    ...  completed  message=hola
    [2:...]   hello:from-flag                    ...  completed  message=hello
    [3:...]   hello:from-flag+                   ...  completed
    [4:...]   hello:from-file-output             ...  completed
    [5:...]   hello:from-file-output             ...  completed
    [6:...]   hello:from-file                    ...  completed  file=.../alt-msg
    [7:...]   hello:from-file                    ...  completed
    [8:...]   hello:from-flag                    ...  completed  message='Howdy Guild!'
    [9:...]   hello:from-flag                    ...  completed
    [10:...]  hello:default                      ...  completed
    [11:...]  gpkg.hello/hello:from-file-output  ...  completed  test-4
    [12:...]  gpkg.hello/hello:from-file         ...  completed  test-3
    [13:...]  gpkg.hello/hello:from-flag         ...  completed  test-2
    [14:...]  gpkg.hello/hello:default           ...  completed  test-1
    <exit 0>

List from the `examples` directory:

    >>> cd("examples")

    >>> run("guild runs -o hello")
    [1:...]   hello:from-flag (hello)            ...  completed  message=hola
    [2:...]   hello:from-flag (hello)            ...  completed  message=hello
    [3:...]   hello:from-flag+ (hello)           ...  completed
    [4:...]   hello:from-file-output (hello)     ...  completed
    [5:...]   hello:from-file-output (hello)     ...  completed
    [6:...]   hello:from-file (hello)            ...  completed  file=.../alt-msg
    [7:...]   hello:from-file (hello)            ...  completed
    [8:...]   hello:from-flag (hello)            ...  completed  message='Howdy Guild!'
    [9:...]   hello:from-flag (hello)            ...  completed
    [10:...]  hello:default (hello)              ...  completed
    [11:...]  gpkg.hello/hello:from-file-output  ...  completed  test-4
    [12:...]  gpkg.hello/hello:from-file         ...  completed  test-3
    [13:...]  gpkg.hello/hello:from-flag         ...  completed  test-2
    [14:...]  gpkg.hello/hello:default           ...  completed  test-1
    <exit 0>
