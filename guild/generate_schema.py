import os
from textwrap import indent
from typing import List, Literal, Union, Dict, Any

import yaml
import pydantic
from pydantic import BaseModel

import guild.guildfile as gf

class GuildfileParsingModel(BaseModel):
    __root__: Union[
        # anonymous model, operations only
        Dict[str, gf.OpDef],
        # full form
        List[Union[
            gf.PackageDef, 
            Dict[Literal["operations"], Dict[str, gf.OpDef]],
            gf.ModelDef, 
        ]]
    ]

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

if __name__ == "__main__":
    fn = os.path.join(os.path.dirname(os.path.dirname(__file__)), "guildfile.schema.json")
    with open(fn, "w") as f:
        f.write(pydantic.schema_json_of(GuildfileParsingModel, indent=2, title="Guildfile full format"))
