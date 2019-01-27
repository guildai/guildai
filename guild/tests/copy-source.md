# Copying source

Source code is copied for each run according to the model `source`
attr.

The function that copies the source is `op_util.copy_source`. For our
tests however, we'll use the private version `_copy_source`, which
provides an interface suitable for testing.

    >>> from guild.op_util import _copy_source

We'll use the sample project `copy-source` to illustrate the supported
copy behavior.

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
    empty e3b0c442
    guild.yml ...
    hello.py 6ae95c9c
    subdir/b.txt 43451775

The `include-logo` model explicitly includes `subdir/logo.png`, which
would otherwise not be copied:

    >>> copy_model_source("include-logo")
    a.txt 90605548
    empty e3b0c442
    guild.yml ...
    hello.py 6ae95c9c
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

## Links

The tests below illustrate how copy source handles symlinks. We need
to generate a test case with links because we can't distribute links
within the Guild source code (Python wheels, used to package Guild,
don't support links).

Here's a directory with various files and links:

    >>> project_dir = mkdtemp()
    >>> def project_file(name, s):
    ...     open(join_path(project_dir, name), "w").write(s)
    >>> def project_link(dest, link):
    ...     symlink(dest, join_path(project_dir, link))
    >>> def project_subdir(path):
    ...     mkdir(join_path(project_dir, path))

    >>> project_file("a.txt", "hello")
    >>> project_link("a.txt", "link-to-a.txt")
    >>> project_subdir("cycle")
    >>> project_file("cycle/b.txt", "yo yo yo")
    >>> project_link("../cycle", "cycle/cycle")

Let's verify that a cycle actually exists:

    >>> exists(join_path(project_dir, *(["cycle"] * 10)))
    True

A proxy for source:

    >>> class Source(object):
    ...     def __init__(self, specs):
    ...         self.specs = specs

A helper to print results:

    >>> def copied_files(dir):
    ...     for path in find(dir):
    ...         print(path, sha256(join_path(dir, path))[:8])

Here's out copied source:

    >>> tmp_dir = mkdtemp()
    >>> _copy_source(project_dir, Source([]), tmp_dir)
    >>> copied_files(tmp_dir)
    a.txt 2cf24dba
    cycle/b.txt c940b581
    link-to-a.txt 2cf24dba

Note that the cycle is handled in the copy.
