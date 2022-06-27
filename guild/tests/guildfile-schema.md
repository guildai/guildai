# Schema validation

Guild's schema is defined in `guild.guildfile_schema`. It should pass
validation for every existing example in our examples folder. Once we
can do that, then we can start treating the schema as a source of
truth for structure, and any new examples must then match the schema.

    >>> from guild import guildfile_schema

## Guild file validation

Helper:

    >>> def validate(name):
    ...     guildfile_path = path(sample("projects", "guildfile-schema", name))
    ...     try:
    ...         guildfile_schema.parse_file(guildfile_path)
    ...     except guildfile_schema.ValidationError as e:
    ...         for err in e.errors():
    ...             print(f"{':'.join(err['loc'])}: [{err['type']}] {err['msg']}")
    ...     else:
    ...         print("ok")

### Invalid root

Guild file root values must be a list or a dict.

    >>> validate("invalid-root.yml")
    __root__: [type_error.dict] value is not a valid dict
    __root__: [type_error.list] value is not a valid list

### Invalid top level ops

Operations defined at the root of the Guild file must be dicts.

    >>> validate("invalid-toplevel-ops.yml")
    __root__:bar: [type_error.dict] value is not a valid dict
    __root__:baz: [type_error.dict] value is not a valid dict
    __root__: [type_error.list] value is not a valid list

TODO: This is arguably an odd edge case, but it looks like the
validation is possibly confusing operation only and full guild file
types. In any case, the last error message above appears wrong - it
ought to complain about 'foo' not being a valid dict. (The term 'valid
dict' here is strange as well, but perhaps this is baked into
Pydantic - the correct error message should be 'value is not a dict'.)

### TODO - lots more to check here!

## Validate example Guild files

To exercise the schema validation and to verify the correctness of our
examples, apply validation to the Gulid files under `examples/`.

    >>> def example_guildfiles():
    ...     return sorted(filter(
    ...         lambda p: os.path.basename(p) == "guild.yml",
    ...         findl(examples_dir())))

    >>> for path in example_guildfiles():  # doctest: +REPORT_UDIFF
    ...     print(path)
    ...     _ = guildfile_schema.parse_file(os.path.join(examples_dir(), path))
    api/guild.yml
    bias/guild.yml
    classification-report/guild.yml
    dependencies/guild.yml
    detectron2/guild.yml
    dvc/guild.yml
    flags/guild.yml
    get-started-use-guild/guild.yml
    hello-package-2/build/lib/gpkg/hello/guild.yml
    hello-package-2/guild.yml
    hello-package-legacy/build/lib/hello/guild.yml
    hello-package-legacy/guild.yml
    hello-package/build/lib/gpkg/hello/guild.yml
    hello-package/guild.yml
    hello/guild.yml
    hydra/guild.yml
    hyperopt/guild.yml
    iris-svm/guild.yml
    keras/guild.yml
    languages/guild.yml
    models/guild.yml
    notebooks/guild.yml
    parallel-runs/build/lib/gpkg/anonymous_f35005fb/guild.yml
    parallel-runs/guild.yml
    pipeline/guild.yml
    project-user-config/guild.yml
    pytest/guild.yml
    pytorch-lightning/guild.yml
    required-operation/guild.yml
    s3-resource/guild.yml
    scalars/guild.yml
    separating-inputs-and-outputs/guild.yml
    sourcecode/guild.yml
    sourcecode/subproject/guild.yml
    tensorboard/guild.yml
    tensorflow-versions/guild.yml
    tensorflow/guild.yml
    tensorflow2/guild.yml
    upstream-flags/guild.yml
    vscode-extension/guild.yml

## Schema generation via CLI

Use the hidden `schema` command to generate the Guildfile schema. This
is useful for editors that support YAML schema validation.

    >>> run("guild schema")
    {
      "title": "Guild File",
      "$ref": "#/definitions/GuildfileParsingModel",
      ...
    }
    <exit 0>
