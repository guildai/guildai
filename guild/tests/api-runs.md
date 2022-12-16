# Guild `api runs` command

Generate some sample runs.

    >>> project = Project(sample("projects", "hello"))

    >>> project.run("hello-file")
    Resolving file
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
            "size": ...,
            "type": "Text file",
            "viewer": "text"
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
