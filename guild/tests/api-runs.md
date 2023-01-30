# Guild `api runs` command

Generate some sample runs.

    >>> use_project("hello")

    >>> run("guild run hello-file -y")
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out

## `api runs`

    >>> run("guild api runs -f")  # doctest: +REPORT_UDIFF
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
            "mtime": ...,
            "operation": null,
            "path": "README.md",
            "run": null,
            "size": 135
          },
          {
            "mtime": ...,
            "operation": null,
            "path": "cat.py",
            "run": null,
            "size": 294
          },
          {
            "mtime": ...,
            "operation": null,
            "path": "guild.yml",
            "run": null,
            "size": 502
          },
          {
            "mtime": ...,
            "operation": null,
            "path": "hello.txt",
            "run": null,
            "size": 20
          },
          {
            "mtime": ...,
            "operation": null,
            "path": "msg.out",
            "run": null,
            "size": ...
          },
          {
            "mtime": ...,
            "operation": null,
            "path": "repeat.py",
            "run": null,
            "size": 103
          },
          {
            "mtime": ...,
            "operation": null,
            "path": "say.py",
            "run": null,
            "size": 36
          }
        ],
        "flags": {
          "file": "hello.txt"
        },
        "id": "...",
        "label": "file=hello.txt",
        "marked": false,
        "opRef": {
          "modelName": "",
          "opName": "hello-file",
          "pkgName": ".../samples/projects/hello/guild.yml",
          "pkgType": "guildfile",
          "pkgVersion": "..."
        },
        "operation": "hello-file",
        "otherAttrs": {},
        "projectDir": ".../samples/projects/hello",
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
          "root": "."
        },
        "started": ...,
        "status": "completed",
        "stopped": ...,
        "tags": []
      }
    ]
    <exit 0>
