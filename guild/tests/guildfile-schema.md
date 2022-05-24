# Guild File Schema

    >>> from guild import guildfile_schema

    >>> print(guildfile_schema.schema_json())  # doctest: +REPORT_UDIFF
    {
      "title": "Guild File",
      "$ref": "#/definitions/GuildfileParsingModel",
      "definitions": {
        "ResourceSourceSchema": {
          "title": "ResourceSourceSchema",
          "type": "object",
          "properties": {
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
            "operation": {
              "title": "Operation",
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
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              ]
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
            "preserve_path": {
              "title": "Preserve Path",
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
            "params": {
              "title": "Params",
              "type": "object",
              "additionalProperties": {
                "type": "string"
              }
            },
            "help": {
              "title": "Help",
              "type": "string"
            }
          }
        },
        "FlagChoiceSchema": {
          "title": "FlagChoiceSchema",
          "type": "object",
          "properties": {
            "alias": {
              "title": "Alias",
              "type": "string"
            },
            "description": {
              "title": "Description",
              "type": "string"
            },
            "value": {
              "title": "Value",
              "type": "string"
            }
          }
        },
        "FlagDefSchema": {
          "title": "FlagDefSchema",
          "type": "object",
          "properties": {
            "allow-other": {
              "title": "Allow-Other",
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
            "arg-name": {
              "title": "Arg-Name",
              "type": "string"
            },
            "arg-skip": {
              "title": "Arg-Skip",
              "type": "string"
            },
            "arg-split": {
              "title": "Arg-Split",
              "type": "string"
            },
            "arg-switch": {
              "title": "Arg-Switch",
              "type": "string"
            },
            "choices": {
              "title": "Choices",
              "default": [],
              "type": "array",
              "items": {
                "$ref": "#/definitions/FlagChoiceSchema"
              }
            },
            "default": {
              "title": "Default",
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "integer"
                },
                {
                  "type": "number"
                },
                {
                  "type": "number"
                },
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
              "type": "string"
            },
            "distribution": {
              "title": "Distribution",
              "type": "string"
            },
            "env-name": {
              "title": "Env-Name",
              "type": "string"
            },
            "extra": {
              "title": "Extra",
              "type": "object"
            },
            "max": {
              "title": "Max",
              "type": "string"
            },
            "min": {
              "title": "Min",
              "type": "string"
            },
            "name": {
              "title": "Name",
              "type": "string"
            },
            "null-label": {
              "title": "Null-Label",
              "type": "string"
            },
            "required": {
              "title": "Required",
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
            "type": {
              "title": "Type",
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        "FileSelectSpecSchema": {
          "title": "FileSelectSpecSchema",
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
        "FileSelectDefSchema": {
          "title": "FileSelectDefSchema",
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
                "$ref": "#/definitions/FileSelectSpecSchema"
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
          },
          "additionalProperties": false
        },
        "PublishDefSchema": {
          "title": "PublishDefSchema",
          "type": "object",
          "properties": {
            "files": {
              "$ref": "#/definitions/FileSelectDefSchema"
            },
            "template": {
              "title": "Template",
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        "OpDefSchema": {
          "title": "OpDefSchema",
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
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              ]
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
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "array",
                  "items": {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "object",
                        "additionalProperties": {
                          "type": "array",
                          "items": {
                            "anyOf": [
                              {
                                "type": "string"
                              },
                              {
                                "$ref": "#/definitions/ResourceSourceSchema"
                              }
                            ]
                          }
                        }
                      }
                    ]
                  }
                }
              ]
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
            "exec": {
              "title": "Exec",
              "default": "",
              "type": "string"
            },
            "flags": {
              "title": "Flags",
              "type": "object",
              "additionalProperties": {
                "anyOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "integer"
                  },
                  {
                    "type": "number"
                  },
                  {
                    "type": "number"
                  },
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
                  },
                  {
                    "$ref": "#/definitions/FlagDefSchema"
                  }
                ]
              }
            },
            "flag-encoder": {
              "title": "Flag-Encoder",
              "type": "string"
            },
            "flags-dest": {
              "title": "Flags-Dest",
              "type": "string"
            },
            "flags-import": {
              "title": "Flags-Import",
              "anyOf": [
                {
                  "enum": [
                    "yes"
                  ],
                  "type": "string"
                },
                {
                  "enum": [
                    "all"
                  ],
                  "type": "string"
                },
                {
                  "enum": [
                    "no"
                  ],
                  "type": "string"
                },
                {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
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
            "name": {
              "title": "Name",
              "default": "",
              "type": "string"
            },
            "objective": {
              "title": "Objective",
              "type": "object",
              "additionalProperties": {
                "type": "string"
              }
            },
            "optimizers": {
              "title": "Optimizers",
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              ]
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
              "$ref": "#/definitions/PublishDefSchema"
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
              "$ref": "#/definitions/FileSelectDefSchema"
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
        "PackageDefSchema": {
          "title": "PackageDefSchema",
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
        "ResourceDefSchema": {
          "title": "ResourceDefSchema",
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
                "$ref": "#/definitions/ResourceSourceSchema"
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
            }
          }
        },
        "ConfigDefSchema": {
          "title": "ConfigDefSchema",
          "description": "This is basically the same as a model, but it serves\nas a template that other models can extend",
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
            "extends": {
              "title": "Extends",
              "default": "",
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              ]
            },
            "guildfile": {
              "title": "Guildfile",
              "default": "",
              "type": "string"
            },
            "config": {
              "title": "Config",
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
              "default": {},
              "type": "object",
              "additionalProperties": {
                "$ref": "#/definitions/OpDefSchema"
              }
            },
            "params": {
              "title": "Params",
              "type": "object",
              "additionalProperties": {
                "type": "string"
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
              "default": {},
              "type": "object",
              "additionalProperties": {
                "$ref": "#/definitions/ResourceDefSchema"
              }
            },
            "sourcecode": {
              "$ref": "#/definitions/FileSelectDefSchema"
            }
          },
          "additionalProperties": false
        },
        "ModelDefSchema": {
          "title": "ModelDefSchema",
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
            "extends": {
              "title": "Extends",
              "default": "",
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              ]
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
              "default": {},
              "type": "object",
              "additionalProperties": {
                "$ref": "#/definitions/OpDefSchema"
              }
            },
            "params": {
              "title": "Params",
              "type": "object",
              "additionalProperties": {
                "type": "string"
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
              "default": {},
              "type": "object",
              "additionalProperties": {
                "$ref": "#/definitions/ResourceDefSchema"
              }
            },
            "sourcecode": {
              "$ref": "#/definitions/FileSelectDefSchema"
            }
          },
          "additionalProperties": false
        },
        "GuildfileParsingModel": {
          "title": "GuildfileParsingModel",
          "description": "Ties together the base types into one of two forms:\n\n- implicit model guildfile, includes only operations\n- \"full\" format, which includes details for Package, Config, and one or more models",
          "anyOf": [
            {
              "type": "object",
              "additionalProperties": {
                "$ref": "#/definitions/OpDefSchema"
              }
            },
            {
              "type": "array",
              "items": {
                "anyOf": [
                  {
                    "$ref": "#/definitions/PackageDefSchema"
                  },
                  {
                    "$ref": "#/definitions/ConfigDefSchema"
                  },
                  {
                    "$ref": "#/definitions/ModelDefSchema"
                  }
                ]
              }
            }
          ]
        }
      }
    }
