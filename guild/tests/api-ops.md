# Guild `api ops` command

Generate some sample runs.

    >>> project = Project(example("hello"))

    >>> project.run("hello-file")
    Resolving file dependency
    Using hello.txt for file resource
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out

## `api ops`

    >>> run(f"guild api ops -f", cwd=project.cwd)  # doctest: +REPORT_UDIFF
    [
      {
        "description": "Say hello to my friends",
        "details": [],
        "flags": [
          "msg: (default is Hello Guild!)"
        ],
        "fullname": "hello",
        "main": "say",
        "model": "",
        "model_name": "",
        "name": "hello"
      },
      {
        "description": "Show a message from a file",
        "details": [],
        "flags": [
          "file: (default is hello.txt)"
        ],
        "fullname": "hello-file",
        "main": "cat",
        "model": "",
        "model_name": "",
        "name": "hello-file"
      },
      {
        "description": "Show a message from a hello-file operation",
        "details": [
          "Relies on the output interface from `hello-file`, which is to write the message to `msg.out`."
        ],
        "flags": [],
        "fullname": "hello-op",
        "main": "cat",
        "model": "",
        "model_name": "",
        "name": "hello-op"
      }
    ]
    <exit 0>
