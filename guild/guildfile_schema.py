from decimal import Decimal
from typing import List, Union, Dict, Any, Optional
from typing_extensions import Literal

import pydantic as schema

optional_bool_type = Optional[Union[bool, Literal["yes"], Literal["no"]]]


def underscore_to_dash(string: str) -> str:
    return string.replace("_", "-")


class FileSelectSpecSchema(schema.BaseModel):
    patterns: List[str] = []
    patterns_type: Optional[str]
    type: Optional[str]
    include: Optional[
        Union[
            str,
            Dict[
                Union[Literal["dir"], Literal["text"], Literal["binary"]],
                Union[str, List[str]],
            ],
        ]
    ]
    exclude: Optional[
        Union[
            str,
            Dict[
                Union[Literal["dir"], Literal["text"], Literal["binary"]],
                Union[str, List[str]],
            ],
        ]
    ]


class FileSelectDefSchema(schema.BaseModel):
    root: Optional[str]
    specs: Optional[List['FileSelectSpecSchema']]
    digest: Optional[str]
    dest: Optional[str]
    empty_def: optional_bool_type = True
    disabled: optional_bool_type

    class Config:
        alias_generator = underscore_to_dash
        arbitrary_types_allowed = True
        extra = 'forbid'


FlagValueTypes = Union[Literal["null"], str, int, float, Decimal, optional_bool_type]


class FlagChoiceSchema(schema.BaseModel):
    alias: Optional[str]
    description: Optional[str]
    value: Optional[str]


class FlagDefSchema(schema.BaseModel):
    allow_other: optional_bool_type
    arg_name: Optional[str]
    arg_skip: Optional[str]
    arg_split: Optional[str]
    arg_switch: Optional[str]
    choices: Optional[List[Union[FlagValueTypes, 'FlagChoiceSchema']]]
    default: Optional[FlagValueTypes]
    description: Optional[str]
    distribution: Optional[str]
    env_name: Optional[str]
    extra: Optional[dict]
    max: Optional[str]
    min: Optional[str]
    name: Optional[str]
    nb_replace: Optional[str]
    null_label: Optional[str]
    required: optional_bool_type
    type: Optional[str]

    class Config:
        alias_generator = underscore_to_dash
        arbitrary_types_allowed = True
        extra = 'forbid'
        underscore_attrs_are_private = True


class PublishDefSchema(schema.BaseModel):
    files: Optional['FileSelectDefSchema']
    template: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        extra = 'forbid'


class OptimizerDefSchema(schema.BaseModel):
    name: Optional[str]
    opspec: Optional[str] = schema.Field("", alias="algorithm")
    default: optional_bool_type = False
    flags: Optional[Dict[str, Union[Literal[None], FlagValueTypes, FlagDefSchema]]]

    class Config:
        arbitrary_types_allowed = True
        extra = 'forbid'


class DvCResourceSchema(schema.BaseModel):
    dvcfile: Optional[str]
    always_pull: optional_bool_type
    remote: Optional[str]
    dvcstage: Optional[str]

    class Config:
        alias_generator = underscore_to_dash
        extra = 'forbid'


resource_types = Union[
    str, 'ResourceSourceSchema', 'ResourceDefSchema', 'DvCResourceSchema'
]
file_types = Union[str, FileSelectDefSchema, FileSelectSpecSchema]
str_or_dict_str_str = Union[str, Dict[str, str]]


class StepSchema(schema.BaseModel):
    run: Optional[str]
    flags: Optional[Dict[str, Union[FlagValueTypes, List[FlagValueTypes]]]]
    optimizer: Optional[Union[str, OptimizerDefSchema]]
    max_trials: Optional[int]


class OpDefSchema(schema.BaseModel):
    can_stage_trials: optional_bool_type
    compare: Optional[Union[str, List[str]]]
    default: optional_bool_type
    default_flag_arg_skip: optional_bool_type
    default_max_trials: Optional[int]
    delete_on_success: optional_bool_type
    disable_plugins: Optional[Union[optional_bool_type, Literal["all"], List[str]]]
    description: Optional[str]
    env: Dict[str, str] = {}
    env_secrets: Optional[str]
    exec_: Optional[str] = schema.Field("", alias="exec")
    flags: Optional[Dict[str, Union[Literal[None], FlagValueTypes, FlagDefSchema]]]
    flag_encoder: Optional[str]
    flags_dest: Optional[str]
    flags_import: Optional[Union[optional_bool_type, Literal["all"], List[str]]]
    flags_import_skip: Optional[List[str]]
    guildfile: Optional[str]
    handle_keyboard_interrupt: optional_bool_type = True
    label: Optional[str]
    main: Optional[str]
    name: str = ""
    notebook: Optional[str]
    objective: Optional[Dict[str, str]]
    optimizers: Optional[Union[str, List[str], Dict[str, OptimizerDefSchema]]]
    output_scalars: Optional[Union[str_or_dict_str_str, List[str_or_dict_str_str]]]
    pip_freeze: Optional[str]
    plugins: Optional[Union[str, List[str], Literal[False]]]
    publish: Optional[PublishDefSchema]
    python_path: Optional[str]
    python_requires: Optional[str]
    references: Optional[Union[str, List[str]]]
    requires: Optional[Union[resource_types, List[resource_types]]]
    run_attrs: Optional[Dict[str, str]]
    set_trace: optional_bool_type
    sourcecode: Optional[Union[optional_bool_type, file_types, List[file_types]]]
    steps: Optional[List[Union[str, StepSchema]]]
    stoppable: optional_bool_type
    tags: List[str] = []

    class Config:
        alias_generator = underscore_to_dash
        arbitrary_types_allowed = True
        extra = 'forbid'
        underscore_attrs_are_private = True


SourceTypes = [
    "config",
    "file",
    "module",
    "url",
]


class ResourceSourceSchema(schema.BaseModel):
    uri: Optional[str] = schema.Field("", alias="url")
    name: Optional[str] = ""
    operation: Optional[str]
    sha256: Optional[str]
    unpack: Optional[bool]
    type: Optional[str]
    select: Optional[Union[str, List[str]]]
    warn_if_empty: bool = True
    fail_if_empty: bool = False
    rename: Optional[Union[str, List[str]]]
    post_process: Optional[str]
    target_path: Optional[str]
    target_type: Optional[str]
    replace_existing: optional_bool_type
    preserve_path: optional_bool_type
    params: Optional[Dict[str, FlagValueTypes]]
    help: Optional[str]
    # used in yaml, do not exist on actual model
    config: Optional[str]
    file: Optional[str]
    module: Optional[str]
    path: Optional[str]

    class Config:
        alias_generator = underscore_to_dash
        extra = 'forbid'


class ResourceDefSchema(schema.BaseModel):
    name: Optional[str]
    fullname: Optional[str]
    flag_name: Optional[str]
    description: Optional[str]
    target_path: Optional[str]
    preserve_path: Optional[str]
    target_type: Optional[str]
    default_unpack: Optional[str]
    private: optional_bool_type
    references: Optional[List[str]]
    sources: List['ResourceSourceSchema'] = []
    source_types: List[str] = SourceTypes + ["operation"]
    default_source_type: str = "file"
    # missing fields that exist in yaml
    file: Optional[str]
    module: Optional[str]

    class Config:
        alias_generator = underscore_to_dash
        arbitrary_types_allowed = True
        extra = 'forbid'


class ModelDefSchema(schema.BaseModel):
    default: optional_bool_type
    description: str = ""
    extra: Dict[str, str] = {}
    extends: Union[str, List[str]] = ""
    guildfile: str = ""
    name: str = schema.Field("", alias="model")
    op_default_config: Optional['OpDefSchema'] = schema.Field(
        alias="operation-defaults"
    )
    operations: Dict[str, 'OpDefSchema'] = {}
    params: Optional[Dict[str, str]]
    parents: List[str] = []
    plugins: Optional[Union[List[str], Literal[False]]] = []
    python_requires: Optional[str]
    references: Optional[List[str]]
    resources: Dict[
        str,
        Union[
            'ResourceSourceSchema',
            'ResourceDefSchema',
            List[Union['ResourceSourceSchema', 'ResourceDefSchema']],
        ],
    ] = {}
    sourcecode: Optional[Union[optional_bool_type, file_types, List[file_types]]]

    class Config:
        alias_generator = underscore_to_dash
        arbitrary_types_allowed = True
        extra = 'forbid'
        underscore_attrs_are_private = True


class ConfigDefSchema(ModelDefSchema):
    """This is basically the same as a model, but it serves
    as a template that other models can extend"""

    name: str = schema.Field("", alias="config")


class OperationDefaultsDefSchema(ModelDefSchema):
    """This is basically the same as a model, but it serves
    as a template that other models can extend"""

    name: str = schema.Field("", alias="operation-defaults")


class PackageDefSchema(schema.BaseModel):
    author: Optional[str]
    author_email: Optional[str]
    data_files: Optional[List[str]]
    description: Optional[str]
    guildfile: Optional[str]
    license: Optional[str]
    name: Optional[str] = schema.Field("", alias="package")
    packages: Optional[List[str]]
    python_requires: Optional[str]
    python_tag: Optional[str]
    requires: Optional[List[str]]
    tags: Optional[List[str]]
    url: Optional[str]
    # These are coerced to strings, but we are lenient in the type here to allow
    # the generated schema to not require quotes around versions in YAML.
    version: Optional[Union[str, int, float]]

    class Config:
        extra = 'forbid'
        alias_generator = underscore_to_dash


class GuildfileParsingModel(schema.BaseModel):
    """Ties together the base types into one of two forms:

    - implicit model guildfile, includes only operations
    - "full" format, which includes details for Package, Config, and one or more models"""

    __root__: Union[
        # anonymous model, operations only
        Dict[str, OpDefSchema],
        # full form
        List[
            Union[
                PackageDefSchema,
                ConfigDefSchema,
                ModelDefSchema,
            ]
        ],
    ]

    def __init__(self, **data: Any) -> None:
        # pylint: disable=useless-super-delegation
        super().__init__(**data)


def schema_json():
    return schema.schema_json_of(GuildfileParsingModel, indent=2, title="Guild File")


def main():
    args = _parse_args()
    out = schema_json()
    if args.file == "-":
        print(out)
    else:
        with open(args.file, "w") as f:
            f.write(out)


def _parse_args():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument(
        "-f",
        "--file",
        help=(
            "Schema file to generate. Use '-' to print schema to "
            "standard output (default)."
        ),
        default="-",
    )
    return p.parse_args()


# See https://github.com/samuelcolvin/pydantic/issues/1298
FileSelectDefSchema.update_forward_refs()
ModelDefSchema.update_forward_refs()
OpDefSchema.update_forward_refs()
OptimizerDefSchema.update_forward_refs()
FlagChoiceSchema.update_forward_refs()
FlagDefSchema.update_forward_refs()
PublishDefSchema.update_forward_refs()
ResourceDefSchema.update_forward_refs()
ResourceSourceSchema.update_forward_refs()

if __name__ == "__main__":
    main()
