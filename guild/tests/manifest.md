# Manifest file support

A Guild manifest file is a flat file log of lines consisting of
shlex-encoded arguments.

Support is provided in `guild.manifest`.

    >>> from guild import manifest

## Writing

To write a manifest, create an instance of `Manifest` with the path to
the target file.

    >>> tmp = mkdtemp()
    >>> m_path = path(tmp, "manifest-1")
    >>> m = manifest.Manifest(m_path, "w")

The path is available via the `path` attribute.

    >>> m.path == m_path, (m.path, m_path)
    (True, ...)

Log entries are written using the `write()` method.

    >>> m.write(["a", "foo", "bar baz"])
    >>> m.write(["a", "red", "green", "red green"])

Close the manifest when done writing using `close()`.

    >>> m.close()

Writing to a closed manifest generates an error.

    >>> m.write(["b", "hello"])
    Traceback (most recent call last):
    ValueError: write to closed file

Contents of the log:

    >>> cat(m_path)
    a foo 'bar baz'
    a red green 'red green'
    <BLANKLINE>

## Reading

To read a manifest, use "r" when creating.

    >>> m = manifest.Manifest(m_path, "r")

The manifest objects is used as an interable for reading each line,
returning the a list of arguments.

    >>> for args in m:
    ...     print(args)
    ['a', 'foo', 'bar baz']
    ['a', 'red', 'green', 'red green']

The `read()` method can alternatively be used to read manifest
entries.

    >>> m = manifest.Manifest(m_path, "r")
    >>> m.read()
    ['a', 'foo', 'bar baz']

    >>> m.read()
    ['a', 'red', 'green', 'red green']

When at the end-of-file, `read()` generates an exception.

    >>> m.read()
    Traceback (most recent call last):
    ValueError: end of file

Close the manifest after reading from it.

    >>> m.close()

Reading from a closed file generates an error.

    >>> m.read()
    Traceback (most recent call last):
    ValueError: readline of closed file

## Context manager interface

A manifest can be used as a context manager, which closes the manifest
when it goes out of context.

    >>> m = manifest.Manifest(m_path, "r")
    >>> with m:
    ...     m.read()
    ['a', 'foo', 'bar baz']

At this point the manifest is closed.

    >>> m.read()
    Traceback (most recent call last):
    ValueError: readline of closed file
