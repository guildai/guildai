# Validate Examples Schema

To exercise the schema validation and to verify the correctness of our
examples, apply validation to the Guild files under `examples/`.

    >>> def example_guildfiles():
    ...     return sorted(filter(
    ...         lambda p: (os.path.basename(p) == "guild.yml" and "/build/" not in p),
    ...         findl(examples_dir())))

    >>> from guild import guildfile_schema
    >>> for path in example_guildfiles():  # doctest: +REPORT_UDIFF
    ...     print(path)
    ...     try:
    ...         _ = guildfile_schema.parse_file(os.path.join(examples_dir(), path))
    ...     except Exception as e:
    ...         print(f"Failure at {path}: {str(e)}")
    api/guild.yml
    bias/guild.yml
    classification-report/guild.yml
    dependencies/guild.yml
    detectron2/guild.yml
    dvc/guild.yml
    flags/guild.yml
    get-started-use-guild/guild.yml
    hello-package-2/guild.yml
    hello-package-legacy/guild.yml
    hello-package/guild.yml
    hello/guild.yml
    hydra/guild.yml
    hyperopt/guild.yml
    iris-svm/guild.yml
    keras/guild.yml
    languages/guild.yml
    models/guild.yml
    notebooks/guild.yml
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
