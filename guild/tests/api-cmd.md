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

## `api runs`

    >>> run("guild -H {} api runs -f".format(project.guild_home))  # doctest: +REPORT_UDIFF
    [
      {
        "command": "... -um guild.op_main cat -- --file hello.txt",
        "comments": [],
        "deps": [],
        "env": {
          ...
        },
        "exitStatus": 0,
        "files": [
          {
            "icon": "file-send",
            "iconTooltip": "Link",
            "mtime": ...,
            "operation": null,
            "path": "hello.txt",
            "run": null,
            "size": 20,
            "type": "Link",
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
        "path": "...",
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
