# Guild `api help-op` command

The `api help-op` command shows operation details as JSON.

    >>> run(f"guild api help-op -f train.py",
    ...     cwd=example("get-started"))  # doctest: +REPORT_UDIFF
    {
      "description": "",
      "flags": {
        "noise": {
          "choices": [],
          "default": 0.1,
          "defaultAssign": "noise=0.1",
          "description": "",
          "type": "number"
        },
        "x": {
          "choices": [],
          "default": 0.1,
          "defaultAssign": "x=0.1",
          "description": "",
          "type": "number"
        }
      },
      "fullname": "train.py",
      "guildfile": {
        "dir": .../examples/get-started",
        "src": null
      },
      "name": "train.py",
      "opref": {
        "modelName": "",
        "opName": "train.py",
        "pkgName": .../examples/get-started",
        "pkgType": "script",
        "pkgVersion": ""
      }
    }
    <exit 0>

    >>> run(f"guild api help-op -f args.py",
    ...     cwd=example("flags"))  # doctest: +REPORT_UDIFF
    {
      "description": "",
      "flags": {
        "b": {
          "choices": [
            {
              "alias": null,
              "description": "",
              "value": true
            },
            {
              "alias": null,
              "description": "",
              "value": false
            }
          ],
          "default": false,
          "defaultAssign": "b=no",
          "description": "",
          "type": null
        },
        "f": {
          "choices": [],
          "default": 1.1,
          "defaultAssign": "f=1.1",
          "description": "",
          "type": "float"
        },
        "i": {
          "choices": [],
          "default": 1,
          "defaultAssign": "i=1",
          "description": "",
          "type": "int"
        },
        "s": {
          "choices": [],
          "default": "hello",
          "defaultAssign": "s=hello",
          "description": "",
          "type": null
        }
      },
      "fullname": "args.py",
      "guildfile": {
        "dir": ".../examples/flags",
        "src": null
      },
      "name": "args.py",
      "opref": {
        "modelName": "",
        "opName": "args.py",
        "pkgName": .../examples/flags",
        "pkgType": "script",
        "pkgVersion": ""
      }
    }
    <exit 0>

    >>> run(f"guild api help-op -f args_click.py",
    ...     cwd=example("flags"))  # doctest: +REPORT_UDIFF
    {
      "description": "",
      "flags": {
        "b": {
          "choices": [],
          "default": false,
          "defaultAssign": "b=no",
          "description": "sample flag",
          "type": "boolean"
        },
        "c": {
          "choices": [
            {
              "alias": null,
              "description": "",
              "value": "red"
            },
            {
              "alias": null,
              "description": "",
              "value": "blue"
            },
            {
              "alias": null,
              "description": "",
              "value": "green"
            },
            {
              "alias": null,
              "description": "",
              "value": "gray"
            }
          ],
          "default": "red",
          "defaultAssign": "c=red",
          "description": "sample choices",
          "type": null
        },
        "f": {
          "choices": [],
          "default": 1.1,
          "defaultAssign": "f=1.1",
          "description": "sample float",
          "type": "float"
        },
        "i": {
          "choices": [],
          "default": 1,
          "defaultAssign": "i=1",
          "description": "sample int",
          "type": "int"
        },
        "s": {
          "choices": [],
          "default": "hello",
          "defaultAssign": "s=hello",
          "description": "sample string",
          "type": "string"
        }
      },
      "fullname": "args_click.py",
      "guildfile": {
        "dir": .../examples/flags",
        "src": null
      },
      "name": "args_click.py",
      "opref": {
        "modelName": "",
        "opName": "args_click.py",
        "pkgName": .../examples/flags",
        "pkgType": "script",
        "pkgVersion": ""
      }
    }
    <exit 0>

    >>> run(f"guild api help-op -f namespace",
    ...     cwd=example("flags"))  # doctest: +REPORT_UDIFF
    {
      "description": "Use a SimpleNamespace for flag values",
      "flags": {
        "b": {
          "choices": [],
          "default": false,
          "defaultAssign": "b=no",
          "description": "",
          "type": "boolean"
        },
        "f": {
          "choices": [],
          "default": 1.123,
          "defaultAssign": "f=1.123",
          "description": "",
          "type": "number"
        },
        "i": {
          "choices": [],
          "default": 123,
          "defaultAssign": "i=123",
          "description": "",
          "type": "number"
        },
        "l": {
          "choices": [],
          "default": "1 2 foo",
          "defaultAssign": "l='1 2 foo'",
          "description": "",
          "type": null
        },
        "s": {
          "choices": [],
          "default": "hello",
          "defaultAssign": "s=hello",
          "description": "",
          "type": "string"
        }
      },
      "fullname": "namespace",
      "guildfile": {
        "dir": .../examples/flags",
        "src": .../examples/flags/guild.yml"
      },
      "name": "namespace",
      "opref": {
        "modelName": "",
        "opName": "namespace",
        "pkgName": .../examples/flags/guild.yml",
        "pkgType": "guildfile",
        "pkgVersion": "17a5b78d3584b2ab57d8e1fe742aa912"
      }
    }
    <exit 0>
