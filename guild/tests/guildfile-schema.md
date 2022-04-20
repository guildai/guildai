# Guild File Schema

    >>> from guild import guildfile_schema

    >>> print(guildfile_schema.schema_json())  # doctest: +REPORT_UDIFF
    {
      "title": "Guild File",
      "$ref": "#/definitions/GuildfileParsingModel",
      "definitions": {
        "guild__resourcedef__ResourceDef": {
          "title": "ResourceDef",
          "type": "object",
          "properties": {
            "name": {
              "title": "Name",
              "type": "string"
            },
            "fullname": {
              "title": "Fullname",
              "type": "string"
            },
            "flag_name": {
              "title": "Flag Name",
              "type": "string"
            },
            "description": {
              "title": "Description",
              "type": "string"
            },
            "target_path": {
              "title": "Target Path",
              "type": "string"
            },
            "preserve_path": {
              "title": "Preserve Path",
              "type": "string"
            },
            "target_type": {
              "title": "Target Type",
              "type": "string"
            },
            "default_unpack": {
              "title": "Default Unpack",
              "type": "string"
            },
            "private": {
              "title": "Private",
              "type": "boolean"
            },
            "references": {
              "title": "References",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "sources": {
              "title": "Sources",
              "default": [],
              "type": "array",
              "items": {
                "$ref": "#/definitions/ResourceSource"
              }
            },
            "source_types": {
              "title": "Source Types",
              "default": [
                "config",
                "file",
                "module",
                "url"
              ],
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "default_source_type": {
              "title": "Default Source Type",
              "default": "file",
              "type": "string"
            }
          }
        },
        "ResourceSource": {
          "title": "ResourceSource",
          "type": "object",
          "properties": {
            "resdef": {
              "$ref": "#/definitions/guild__resourcedef__ResourceDef"
            },
            "uri": {
              "title": "Uri",
              "default": "",
              "type": "string"
            },
            "name": {
              "title": "Name",
              "default": "",
              "type": "string"
            },
            "sha256": {
              "title": "Sha256",
              "type": "string"
            },
            "unpack": {
              "title": "Unpack",
              "type": "boolean"
            },
            "type": {
              "title": "Type",
              "type": "string"
            },
            "select": {
              "title": "Select",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "warn_if_empty": {
              "title": "Warn If Empty",
              "default": true,
              "type": "boolean"
            },
            "fail_if_empty": {
              "title": "Fail If Empty",
              "default": false,
              "type": "boolean"
            },
            "rename": {
              "title": "Rename",
              "type": "array",
              "items": {
                "type": "array",
                "items": [
                  {
                    "title": "Pattern"
                  },
                  {
                    "title": "Repl"
                  }
                ],
                "minItems": 2,
                "maxItems": 2
              }
            },
            "post_process": {
              "title": "Post Process",
              "type": "string"
            },
            "target_path": {
              "title": "Target Path",
              "type": "string"
            },
            "target_type": {
              "title": "Target Type",
              "type": "string"
            },
            "replace_existing": {
              "title": "Replace Existing",
              "default": false,
              "type": "boolean"
            },
            "preserve_path": {
              "title": "Preserve Path",
              "default": false,
              "type": "boolean"
            },
            "params": {
              "title": "Params",
              "default": {},
              "type": "object"
            },
            "help": {
              "title": "Help",
              "type": "string"
            }
          }
        },
        "FileSelectSpec": {
          "title": "FileSelectSpec",
          "type": "object",
          "properties": {
            "patterns": {
              "title": "Patterns",
              "default": [],
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "patterns_type": {
              "title": "Patterns Type",
              "type": "string"
            },
            "type": {
              "title": "Type",
              "type": "string"
            }
          }
        },
        "FileSelectDef": {
          "title": "FileSelectDef",
          "type": "object",
          "properties": {
            "root": {
              "title": "Root",
              "type": "string"
            },
            "specs": {
              "title": "Specs",
              "type": "array",
              "items": {
                "$ref": "#/definitions/FileSelectSpec"
              }
            },
            "digest": {
              "title": "Digest",
              "type": "string"
            },
            "dest": {
              "title": "Dest",
              "type": "string"
            },
            "empty_def": {
              "title": "Empty Def",
              "default": true,
              "anyOf": [
                {
                  "type": "boolean"
                },
                {
                  "enum": [
                    "yes"
                  ],
                  "type": "string"
                },
                {
                  "enum": [
                    "no"
                  ],
                  "type": "string"
                }
              ]
            },
            "disabled": {
              "title": "Disabled",
              "anyOf": [
                {
                  "type": "boolean"
                },
                {
                  "enum": [
                    "yes"
                  ],
                  "type": "string"
                },
                {
                  "enum": [
                    "no"
                  ],
                  "type": "string"
                }
              ]
            }
          }
        },
        "ModelDef": {
          "title": "ModelDef",
          "type": "object",
          "properties": {
            "default": {
              "title": "Default",
              "anyOf": [
                {
                  "type": "boolean"
                },
                {
                  "enum": [
                    "yes"
                  ],
                  "type": "string"
                },
                {
                  "enum": [
                    "no"
                  ],
                  "type": "string"
                }
              ]
            },
            "description": {
              "title": "Description",
              "default": "",
              "type": "string"
            },
            "extra": {
              "title": "Extra",
              "default": {},
              "type": "object",
              "additionalProperties": {
                "type": "string"
              }
            },
            "guildfile": {
              "title": "Guildfile",
              "default": "",
              "type": "string"
            },
            "model": {
              "title": "Model",
              "default": "",
              "type": "string"
            },
            "op-default-config": {
              "title": "Op-Default-Config",
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "object"
                }
              ]
            },
            "operations": {
              "title": "Operations",
              "default": [],
              "type": "array",
              "items": {
                "$ref": "#/definitions/OpDef"
              }
            },
            "parents": {
              "title": "Parents",
              "default": [],
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "plugins": {
              "title": "Plugins",
              "default": [],
              "anyOf": [
                {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                {
                  "enum": [
                    false
                  ],
                  "type": "boolean"
                }
              ]
            },
            "python-requires": {
              "title": "Python-Requires",
              "type": "string"
            },
            "references": {
              "title": "References",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "resources": {
              "title": "Resources",
              "default": [],
              "type": "array",
              "items": {
                "$ref": "#/definitions/guild__guildfile__ResourceDef"
              }
            },
            "sourcecode": {
              "$ref": "#/definitions/FileSelectDef"
            }
          },
          "additionalProperties": false
        },
        "guild__guildfile__ResourceDef": {
          "title": "ResourceDef",
          "type": "object",
          "properties": {
            "name": {
              "title": "Name",
              "type": "string"
            },
            "fullname": {
              "title": "Fullname",
              "type": "string"
            },
            "flag_name": {
              "title": "Flag Name",
              "type": "string"
            },
            "description": {
              "title": "Description",
              "type": "string"
            },
            "target_path": {
              "title": "Target Path",
              "type": "string"
            },
            "preserve_path": {
              "title": "Preserve Path",
              "type": "string"
            },
            "target_type": {
              "title": "Target Type",
              "type": "string"
            },
            "default_unpack": {
              "title": "Default Unpack",
              "type": "string"
            },
            "private": {
              "title": "Private",
              "type": "boolean"
            },
            "references": {
              "title": "References",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "sources": {
              "title": "Sources",
              "default": [],
              "type": "array",
              "items": {
                "$ref": "#/definitions/ResourceSource"
              }
            },
            "source_types": {
              "title": "Source Types",
              "default": [
                "config",
                "file",
                "module",
                "url",
                "operation"
              ],
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "default_source_type": {
              "title": "Default Source Type",
              "default": "file",
              "type": "string"
            },
            "modeldef": {
              "$ref": "#/definitions/ModelDef"
            }
          }
        },
        "OpDependencyDef": {
          "title": "OpDependencyDef",
          "type": "object",
          "properties": {
            "spec": {
              "title": "Spec",
              "type": "string"
            },
            "description": {
              "title": "Description",
              "type": "string"
            },
            "inline_resource": {
              "$ref": "#/definitions/guild__guildfile__ResourceDef"
            },
            "opdef": {
              "$ref": "#/definitions/OpDef"
            },
            "modeldef": {
              "$ref": "#/definitions/ModelDef"
            }
          }
        },
        "PublishDef": {
          "title": "PublishDef",
          "type": "object",
          "properties": {
            "opdef": {
              "$ref": "#/definitions/OpDef"
            },
            "files": {
              "$ref": "#/definitions/FileSelectDef"
            },
            "template": {
              "title": "Template",
              "type": "string"
            }
          }
        },
        "OpDef": {
          "title": "OpDef",
          "type": "object",
          "properties": {
            "can-stage-trials": {
              "title": "Can-Stage-Trials",
              "anyOf": [
                {
                  "type": "boolean"
                },
                {
                  "enum": [
                    "yes"
                  ],
                  "type": "string"
                },
                {
                  "enum": [
                    "no"
                  ],
                  "type": "string"
                }
              ]
            },
            "compare": {
              "title": "Compare",
              "type": "string"
            },
            "default": {
              "title": "Default",
              "anyOf": [
                {
                  "type": "boolean"
                },
                {
                  "enum": [
                    "yes"
                  ],
                  "type": "string"
                },
                {
                  "enum": [
                    "no"
                  ],
                  "type": "string"
                }
              ]
            },
            "default-flag-arg-skip": {
              "title": "Default-Flag-Arg-Skip",
              "anyOf": [
                {
                  "type": "boolean"
                },
                {
                  "enum": [
                    "yes"
                  ],
                  "type": "string"
                },
                {
                  "enum": [
                    "no"
                  ],
                  "type": "string"
                }
              ]
            },
            "default-max-trials": {
              "title": "Default-Max-Trials",
              "type": "integer"
            },
            "delete-on-success": {
              "title": "Delete-On-Success",
              "anyOf": [
                {
                  "type": "boolean"
                },
                {
                  "enum": [
                    "yes"
                  ],
                  "type": "string"
                },
                {
                  "enum": [
                    "no"
                  ],
                  "type": "string"
                }
              ]
            },
            "requires": {
              "title": "Requires",
              "default": [],
              "type": "array",
              "items": {
                "$ref": "#/definitions/OpDependencyDef"
              }
            },
            "description": {
              "title": "Description",
              "type": "string"
            },
            "env": {
              "title": "Env",
              "default": {},
              "type": "object",
              "additionalProperties": {
                "type": "string"
              }
            },
            "env-secrets": {
              "title": "Env-Secrets",
              "type": "string"
            },
            "exec-": {
              "title": "Exec-",
              "type": "string"
            },
            "flag-encoder": {
              "title": "Flag-Encoder",
              "type": "string"
            },
            "flags-dest": {
              "title": "Flags-Dest",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "flags-import": {
              "title": "Flags-Import",
              "anyOf": [
                {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                {
                  "type": "string"
                }
              ]
            },
            "flags-import-skip": {
              "title": "Flags-Import-Skip",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "guildfile": {
              "title": "Guildfile",
              "type": "string"
            },
            "handle-keyboard-interrupt": {
              "title": "Handle-Keyboard-Interrupt",
              "default": true,
              "anyOf": [
                {
                  "type": "boolean"
                },
                {
                  "enum": [
                    "yes"
                  ],
                  "type": "string"
                },
                {
                  "enum": [
                    "no"
                  ],
                  "type": "string"
                }
              ]
            },
            "label": {
              "title": "Label",
              "type": "string"
            },
            "main": {
              "title": "Main",
              "type": "string"
            },
            "modeldef": {
              "$ref": "#/definitions/ModelDef"
            },
            "name": {
              "title": "Name",
              "default": "",
              "type": "string"
            },
            "objective": {
              "title": "Objective",
              "type": "string"
            },
            "output-scalars": {
              "title": "Output-Scalars",
              "type": "string"
            },
            "pip-freeze": {
              "title": "Pip-Freeze",
              "type": "string"
            },
            "plugins": {
              "title": "Plugins",
              "anyOf": [
                {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                {
                  "enum": [
                    false
                  ],
                  "type": "boolean"
                }
              ]
            },
            "publish": {
              "$ref": "#/definitions/PublishDef"
            },
            "python-path": {
              "title": "Python-Path",
              "type": "string"
            },
            "python-requires": {
              "title": "Python-Requires",
              "type": "string"
            },
            "run-attrs": {
              "title": "Run-Attrs",
              "type": "string"
            },
            "set-trace": {
              "title": "Set-Trace",
              "anyOf": [
                {
                  "type": "boolean"
                },
                {
                  "enum": [
                    "yes"
                  ],
                  "type": "string"
                },
                {
                  "enum": [
                    "no"
                  ],
                  "type": "string"
                }
              ]
            },
            "sourcecode": {
              "$ref": "#/definitions/FileSelectDef"
            },
            "steps": {
              "title": "Steps",
              "type": "array",
              "items": {
                "type": "object"
              }
            },
            "stoppable": {
              "title": "Stoppable",
              "anyOf": [
                {
                  "type": "boolean"
                },
                {
                  "enum": [
                    "yes"
                  ],
                  "type": "string"
                },
                {
                  "enum": [
                    "no"
                  ],
                  "type": "string"
                }
              ]
            },
            "tags": {
              "title": "Tags",
              "default": [],
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "additionalProperties": false
        },
        "PackageDef": {
          "title": "PackageDef",
          "type": "object",
          "properties": {
            "author": {
              "title": "Author",
              "type": "string"
            },
            "author-email": {
              "title": "Author-Email",
              "type": "string"
            },
            "data-files": {
              "title": "Data-Files",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "description": {
              "title": "Description",
              "type": "string"
            },
            "guildfile": {
              "title": "Guildfile",
              "type": "string"
            },
            "license": {
              "title": "License",
              "type": "string"
            },
            "package": {
              "title": "Package",
              "default": "",
              "type": "string"
            },
            "packages": {
              "title": "Packages",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "python-requires": {
              "title": "Python-Requires",
              "type": "string"
            },
            "python-tag": {
              "title": "Python-Tag",
              "type": "string"
            },
            "requires": {
              "title": "Requires",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "tags": {
              "title": "Tags",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "url": {
              "title": "Url",
              "type": "string"
            },
            "version": {
              "title": "Version",
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "integer"
                },
                {
                  "type": "number"
                }
              ]
            }
          },
          "additionalProperties": false
        },
        "GuildfileParsingModel": {
          "title": "GuildfileParsingModel",
          "anyOf": [
            {
              "type": "object",
              "additionalProperties": {
                "$ref": "#/definitions/OpDef"
              }
            },
            {
              "type": "array",
              "items": {
                "anyOf": [
                  {
                    "$ref": "#/definitions/PackageDef"
                  },
                  {
                    "type": "object",
                    "additionalProperties": {
                      "type": "object",
                      "additionalProperties": {
                        "$ref": "#/definitions/OpDef"
                      }
                    }
                  },
                  {
                    "$ref": "#/definitions/ModelDef"
                  }
                ]
              }
            }
          ]
        }
      }
    }
