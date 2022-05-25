# Schema validation

Guild's schema is defined in guild.guildfile_schema. It should pass validation for
every existing example in our examples folder. Once we can do that, then we can start
treating the schema as a source of truth for structure, and any new examples must then
match the schema.

`guild.guildfile_schema`:

    >>> from guild.guildfile_schema import GuildfileParsingModel
    >>> from pydantic import ValidationError
    >>> import yaml
    >>> import os
    >>> for root, dirs, files in os.walk(example("")):
    ...     for f in files:
    ...         if f != "guild.yml":
    ...             continue
    ...         gf_path = os.path.join(root, f)
    ...         if os.path.exists(gf_path):
    ...             with open(gf_path) as fh:
    ...                 obj = yaml.safe_load(fh)
    ...                 try:
    ...                     a=GuildfileParsingModel.parse_obj(obj)
    ...                 except ValidationError as e:
    ...                     sys.exit(f"Validation error in {gf_path}: {e}")
