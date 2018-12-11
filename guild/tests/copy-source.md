# Copying source

Source code is copied for each run according to the model `source`
attr.

The function that copies the source is `op_util.copy_source`. For our
tests however, we'll use the private version `_copy_source`, which
provides an interface suitable for testing.

    >>> from guild.op_util import _copy_source

We'll use the sample project `copy-source` to illustrate the supported
copy behavior.

    >>> from guild import guildfile
    >>> gf = guildfile.from_dir(sample("projects/copy-source"))

The project contains these models:

    >>> sorted(gf.models)
    ['default', 'exclude-all', 'include-logo', 'only-py', 'py-and-guild']

We'll use temporary run directories to test each copy
operation. Here's a helper function that copies the source for the
applicable model and prints the copied source files.

    >>> def copy_model_source(model_name):
    ...     model = gf.models[model_name]
    ...     temp_dir = mkdtemp()
    ...     _copy_source(gf.dir, model.source, temp_dir)
    ...     copied = find(temp_dir)
    ...     if not copied:
    ...         print("<empty>")
    ...         return
    ...     for path in copied:
    ...         print(path, sha256(join_path(temp_dir, path))[:8])

By default, all text files are copied, including links and files
within linked directories:

    >>> copy_model_source("default")
    a.txt 90605548
    cycle/a.txt 5891b5b5
    empty e3b0c442
    guild.yml ...
    hello.py 6ae95c9c
    link-to-a.txt 90605548
    link-to-subdir/b.txt 43451775
    subdir/b.txt 43451775

The `include-logo` model explicitly includes `subdir/logo.png`, which
would otherwise not be copied:

    >>> copy_model_source("include-logo")
    a.txt 90605548
    cycle/a.txt 5891b5b5
    empty e3b0c442
    guild.yml ...
    hello.py 6ae95c9c
    link-to-a.txt 90605548
    link-to-subdir/b.txt 43451775
    subdir/b.txt 43451775
    subdir/logo.png 4a9bf008

The `exclude-all` model excludes all source and therefore copies
nothing:

    >>> copy_model_source("exclude-all")
    <empty>

The `only-py` model specifies that only `*.py` files be copied:

    >>> copy_model_source("only-py")
    hello.py 6ae95c9c

The `py-and-guild` model specifies Python source and the Guild file:

    >>> copy_model_source("py-and-guild")
    guild.yml ...
    hello.py 6ae95c9c
