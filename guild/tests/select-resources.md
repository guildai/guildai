# Selecting resources

These tests cover `guild.resolver._resolve_source_dir_files`, which is
responsible for selecting files from a directory according the rules
specified in a resource source.

    >>> from guild.resolver import _resolve_source_dir_files

For our tests we'll use the samples files in `select-files`:

    >>> samples_dir = sample("select-files")

Here's a Guild file that defines a resource `r` with multiple sources:

    >>> gf = guildfile.for_string("""
    ... - model: m
    ...   resources:
    ...     r:
    ...       sources:
    ...         - file: {samples_dir}
    ...           select: a.*
    ...         - file: {samples_dir}
    ...           select: b
    ...         - file: {samples_dir}
    ...           select-max: a-([0-9]+)
    ...         - file: {samples_dir}
    ...           select-min: a-(.+)
    ... """.format(samples_dir=samples_dir))

The resource sources for:

    >>> r1_sources = gf.default_model.get_resource("r").sources
    >>> r1_sources
    [<guild.resourcedef.ResourceSource 'file:.../samples/select-files'>]

The files selected for each source:

    >>> for src in r1_sources:
    ...   print("---")
    ...   print(src.select)
    ...   pprint(_resolve_source_dir_files(samples_dir, src))
    ---
    [SelectSpec(pattern='a.*', reduce=None)]
    ['.../samples/select-files/a',
     '.../samples/select-files/a-001',
     '.../samples/select-files/a-1',
     '.../samples/select-files/a-2',
     '.../samples/select-files/a-20']
    ---
    [SelectSpec(pattern='b', reduce=None)]
    ['.../samples/select-files/b']
    ---
    [SelectSpec(pattern='a-([0-9]+)', reduce=<function _select_reduce_max ...>)]
    ['.../samples/select-files/a-20']
    ---
    [SelectSpec(pattern='a-(.+)', reduce=<function _select_reduce_min ...)]
    ['.../samples/select-files/a-001']
