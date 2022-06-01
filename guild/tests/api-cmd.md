# Guild `api` command

Generate some sample runs.

    >>> project = Project(example("hello"))

    >>> project.run("hello-file")
    Resolving file dependency
    Using hello.txt for file resource
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out

Helper for running commands for the project.

    >>> def project_cmd(cmd):
    ...     run(f"guild -H {project.guild_home} {cmd}", cwd=project.cwd)

## `api runs`

    >>> project_cmd("api runs -f")  # doctest: +REPORT_UDIFF
    [
      {
        "command": "... -um guild.op_main cat -- --file hello.txt",
        "comments": [],
        "deps": [],
        "dir": "...",
        "env": {
          ...
        },
        "exitStatus": 0,
        "files": [
          {
            "icon": "file-document",
            "iconTooltip": "Text file",
            "mtime": ...,
            "operation": null,
            "path": "hello.txt",
            "run": null,
            "size": 20,
            "type": "Text file",
            "viewer": "text"
          },
          {
            "icon": "file-document",
            "iconTooltip": "Text file",
            "mtime": ...,
            "operation": null,
            "path": "msg.out",
            "run": null,
            "size": 20,
            "type": "Text file",
            "viewer": "text"
          }
        ],
        "flags": {
          "file": "hello.txt"
        },
        "id": "...",
        "label": "file=hello.txt",
        "opModel": "",
        "opName": "hello-file",
        "operation": "hello-file",
        "otherAttrs": {},
        "scalars": [],
        "shortId": "...",
        "sourcecode": {
          "files": [
            "README.md",
            "cat.py",
            "guild.yml",
            "hello.txt",
            "repeat.py",
            "say.py"
          ],
          "root": ".guild/sourcecode"
        },
        "started": "...",
        "status": "completed",
        "stopped": "...",
        "tags": "",
        "time": "0:00:..."
      }
    ]
    <exit 0>

## `api ops`

    >>> project_cmd("api ops -f")  # doctest: +REPORT_UDIFF
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

## `api compare`

    >>> project_cmd("api compare -f")  # doctest: +REPORT_UDIFF
    [
      [
        "run",
        "operation",
        "started",
        "time",
        "status",
        "label",
        "file"
      ],
      [
        "...",
        "hello-file",
        "...",
        "0:00:...",
        "completed",
        "file=hello.txt",
        "hello.txt"
      ]
    ]
    <exit 0>
