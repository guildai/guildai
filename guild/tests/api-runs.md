# Guild `api runs` command

Generate some sample runs.

    >>> project = Project(sample("projects", "hello"))

    >>> project.run("hello-file")
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out

Helper for running commands for the project.

    >>> def project_cmd(cmd):
    ...     run(f"guild -H {project.guild_home} {cmd}", cwd=project.cwd)

## `api runs`

    >>> project_cmd("api runs -f")
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
            "size": 20
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
          "pkgName": ".../guild/tests/samples/projects/hello/guild.yml",
          "pkgType": "guildfile",
          "pkgVersion": "..."
        },
        "operation": "hello-file",
        "otherAttrs": {},
        "projectDir": ".../guild/tests/samples/projects/hello",
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
