# Guild `api ops` command

Generate some sample runs.

    >>> project = Project(sample("projects", "hello"))

    >>> project.run("hello-file")
    Reading message from hello.txt
    Hello, from a file!
    <BLANKLINE>
    Saving message to msg.out

## `api ops`

    >>> run(f"guild api ops -f", cwd=project.cwd)  # doctest: +REPORT_UDIFF
    [
      {
        "description": "Say hello to my friends",
        "flags": {
          "msg": {
            "choices": [],
            "default": "Hello Guild!",
            "defaultAssign": "msg='Hello Guild!'",
            "description": "",
            "type": "string"
          }
        },
        "fullname": "hello",
        "guildfile": {
          "dir": ".../samples/projects/hello",
          "src": ".../samples/projects/hello/guild.yml"
        },
        "name": "hello",
        "opref": {
          "modelName": "",
          "opName": "hello",
          "pkgName": ".../samples/projects/hello/guild.yml",
          "pkgType": "guildfile",
          "pkgVersion": "08585644f5a54d1efea04ecdf1b666b0"
        }
      },
      {
        "description": "Show a message from a file",
        "flags": {
          "file": {
            "choices": [],
            "default": "hello.txt",
            "defaultAssign": "file=hello.txt",
            "description": "",
            "type": null
          }
        },
        "fullname": "hello-file",
        "guildfile": {
          "dir": ".../samples/projects/hello",
          "src": ".../samples/projects/hello/guild.yml"
        },
        "name": "hello-file",
        "opref": {
          "modelName": "",
          "opName": "hello-file",
          "pkgName": ".../samples/projects/hello/guild.yml",
          "pkgType": "guildfile",
          "pkgVersion": "08585644f5a54d1efea04ecdf1b666b0"
        }
      },
      {
        "description": "Show a message from a hello-file operation...",
        "flags": {
          "op": {
            "choices": [],
            "default": null,
            "defaultAssign": "op=null",
            "description": "",
            "type": "string"
          }
        },
        "fullname": "hello-op",
        "guildfile": {
          "dir": ".../samples/projects/hello",
          "src": ".../samples/projects/hello/guild.yml"
        },
        "name": "hello-op",
        "opref": {
          "modelName": "",
          "opName": "hello-op",
          "pkgName": ".../samples/projects/hello/guild.yml",
          "pkgType": "guildfile",
          "pkgVersion": "08585644f5a54d1efea04ecdf1b666b0"
        }
      }
    ]
    <exit 0>
