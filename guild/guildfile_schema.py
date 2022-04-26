from typing import List, Union, Dict, Any
from typing_extensions import Literal

import pydantic as schema

from guild import guildfile


class GuildfileParsingModel(schema.BaseModel):
    __root__: Union[
        # anonymous model, operations only
        Dict[str, guildfile.OpDef],
        # full form
        List[
            Union[
                guildfile.PackageDef,
                Dict[Literal["operations"], Dict[str, guildfile.OpDef]],
                guildfile.ModelDef,
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


if __name__ == "__main__":
    main()
