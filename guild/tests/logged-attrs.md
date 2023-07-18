# Logged Run Attributes

Run attributes are logged using TF event files ending with
`.attrs`. They are written to the log files as text summaries.

Create a directory to log attributes in.

    >>> tmp = mkdtemp()

Use Guild's summary support to write text summaries.

    >>> from guild import summary

Open a writer for an summary event file with a suffix of `.attrs`.

    >>> attrs = summary.SummaryWriter(tmp, filename_suffix=".attrs")

Log text summaries. Guild uses these as text attributes.

    >>> attrs.add_text("color", "red")
    >>> attrs.add_text("height", "tall")
    >>> attrs.add_text("width", "100")
    >>> attrs.close()

Use Guild's TF event support to read the attributes.

    >>> from guild import tfevent

    >>> for name, val in tfevent.AttrReader(tmp):
    ...     print(name, val)
    color red
    height tall
    width 100

Guild's index support provides a way to read logged attributes.

Create a run for the log dir.

    >>> from guild import run as runlib

    >>> run = runlib.for_dir(tmp)

## `guild.index` and run attributes

Use `guild.index` to read the logged attributes.

    >>> from guild import index

    >>> for name, val in sorted(index.logged_attrs(run).items()):
    ...     print(name, val)
    color red
    height tall
    width 100

## Subdirectories

Guild treats subdirectories as attribute name prefixes when reading
logged attributes.

    >>> mkdir(path(tmp, "subdir"))

    >>> attrs = summary.SummaryWriter(path(tmp, "subdir"), filename_suffix=".attrs")

    >>> attrs.add_text("foo", "123")
    >>> attrs.add_text("bar", "hello")
    >>> attrs.close()

    >>> for name, val in sorted(index.logged_attrs(run).items()):
    ...     print(name, val)
    color red
    height tall
    subdir#bar hello
    subdir#foo 123
    width 100
