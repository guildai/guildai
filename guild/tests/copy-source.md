skip-windows: yes

# Copying source

Source code is copied for each run according to the model
`snapshot-source` attr.

The function that copies the source is `op_util.copy_source`. For our
tests however, we'll use the private version `copy_source`, which
provides an interface suitable for testing.

    >>> from guild.op_util import copy_source

We'll use the sample project `copy-source` to illustrate the supported
copy behavior.

    >>> gf = guildfile.from_dir(sample("projects/copy-source"))

The project contains these models:

    >>> sorted(gf.models)
    ['default', 'exclude-all', 'include-logo', 'model-and-op',
     'only-py-1', 'only-py-2', 'py-and-guild']

We'll use temporary run directories to test each copy
operation. Here's a helper function that copies the source for the
applicable model and prints the copied source files.

    >>> def copy_model_source(model_name, op_name=None):
    ...     model = gf.models[model_name]
    ...     source_config = [model.source]
    ...     if op_name:
    ...         source_config.append(model[op_name].source)
    ...     temp_dir = mkdtemp()
    ...     copy_source(gf.dir, source_config, temp_dir)
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

    >>> copy_model_source("only-py-1")
    hello.py 6ae95c9c

    >>> copy_model_source("only-py-2")
    hello.py 6ae95c9c

The `py-and-guild` model specifies Python source and the Guild file:

    >>> copy_model_source("py-and-guild")
    guild.yml ...
    hello.py 6ae95c9c

The `model-and-op` model include a model source spec and a source
spec. These two specs are applied with the op spec being appended to
the model spec.

In this example, the model includes `logo.png` and the op exclude
`*.py` and `a.*` files.

    >>> copy_model_source("model-and-op", "op")
    empty e3b0c442
    guild.yml ...
    subdir/b.txt 43451775
    subdir/logo.png 4a9bf008

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

A helper to print results:

    >>> def copied_files(dir):
    ...     for path in find(dir):
    ...         print(path, sha256(join_path(dir, path))[:8])

Here's out copied source:

    >>> tmp_dir = mkdtemp()
    >>> copy_source(project_dir, guildfile.SourceDef([], None), tmp_dir)
    >>> copied_files(tmp_dir)
    a.txt 2cf24dba
    cycle/b.txt c940b581
    link-to-a.txt 2cf24dba

Note that the cycle is handled in the copy.

## Safeguards

Guild has two safeguards used to avoid incorrectly copying source
files when config is not explicitly provided:

- Skips files larger than 1M
- Copies at most 100 files

To test these measures, let's create a project containing a single
large file and many smaller files:

    >>> project_dir = mkdtemp()

A large file:

    >>> f = open(path(project_dir, "big.txt"), "w")
    >>> _witten = f.write("0" * (1024 * 1024 + 1))

Many small files:

    >>> for i in range(110):
    ...     f = open(path(project_dir, "small-%0.3i.txt" % (i + 1)), "w")
    ...     _written = f.write("")

Our file project files:

    >>> project_files = find(project_dir)

    >>> len(project_files)
    111

    >>> project_files
    ['big.txt',
     'small-001.txt',
     ...
     'small-110.txt']

### Copying without explicit config

Copy the source without config:

    >>> tmp_dir = mkdtemp()
    >>> with LogCapture() as logs:
    ...     copy_source(project_dir, guildfile.SourceDef([], None), tmp_dir)

Logs:

    >>> logs.print_all()
    WARNING: Skipping potential source file .../big.txt because it's too big.
    WARNING: Found 110 source files using default snapshot-source config but
    will only copy 100 as a safety measure.

And the copied files:

    >>> copied = find(tmp_dir)
    >>> len(copied)
    100

    >>> copied
    ['small-001.txt',
     ...
     'small-100.txt']

 We can improve our logged error message by providing an OpDef to
 `copy_source`.

    >>> gf = guildfile.from_string("""
    ... - model: m1
    ...   operations:
    ...     op: {}
    ... """)

Copy the source without config:

    >>> tmp_dir = mkdtemp()
    >>> with LogCapture() as logs:
    ...     copy_source(
    ...         project_dir,
    ...         guildfile.SourceDef([], None),
    ...         tmp_dir,
    ...         gf.default_model["op"])

Now our logs contain some advice to the user:

    >>> logs.print_all()
    WARNING: Skipping potential source file .../big.txt because it's too big.
    To control which source files are copied, specify snapshot-source for
    m1:op.
    WARNING: Found 110 source files using default snapshot-source config but
    will only copy 100 as a safety measure. To control which source files are
    copied, specify snapshot-source for m1:op.

And the files:

    >>> find(tmp_dir)
    ['small-001.txt',
     ...
     'small-100.txt']

### Copying with config

Let's copy the source with config that explicitly enables all files:

    >>> include_all = guildfile.SourceDef([{"include": "*"}], None)

    >>> tmp_dir = mkdtemp()
    >>> with LogCapture() as logs:
    ...     copy_source(project_dir, include_all, tmp_dir)

Nothing logged;

    >>> logs.print_all()

And all files are copied:

    >>> copied = find(tmp_dir)
    >>> len(copied)
    111

    >>> copied
    ['big.txt',
     'small-001.txt',
     ...
     'small-110.txt']

Markdown finished at Tue May 14 13:25:02
