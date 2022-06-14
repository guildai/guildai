# Autocompleteion support

Autocompletion support is provided by `guild.commands.ac_support`.

    >>> from guild.commands import ac_support

These tests break the module abstraction to test internal
functions. For tests of the public CLI interface, see
`autocomplete-xxx.md` files.

## List directories

Directory listing is provided by the `_list_dir` function.

    >>> list_dir = ac_support._list_dir

Create a directory structure to test.

    >>> tmp = mkdtemp()
    >>> touch(path(tmp, "foo.txt"))
    >>> touch(path(tmp, "bar.md"))
    >>> mkdir(path(tmp, "subdir-1"))
    >>> touch(path(tmp, "subdir-1", "baz.bin"))
    >>> touch(path(tmp, "subdir-1", "zed.out"))
    >>> mkdir(path(tmp, "subdir-1", "subdir-2"))

Default listing (no filters):

    >>> list_dir(tmp)
    ['bar.md', 'foo.txt', 'subdir-1/']

    >>> list_dir(path(tmp, "subdir-1"))
    ['baz.bin', 'zed.out', 'subdir-2/']

Filter by extension:

    >>> list_dir(tmp, ext=["txt"])
    ['foo.txt', 'subdir-1/']

    >>> list_dir(tmp, ext=["txt", "md"])
    ['bar.md', 'foo.txt', 'subdir-1/']

    >>> list_dir(tmp, ext=["py", "Md"])
    ['bar.md', 'subdir-1/']

    >>> list_dir(tmp, ext=["TXT"])
    ['foo.txt', 'subdir-1/']

    >>> list_dir(path(tmp, "subdir-1"), ext=["txt"])
    ['subdir-2/']

    >>> list_dir(path(tmp, "subdir-1"), ext=["BIN", "ouT"])
    ['baz.bin', 'zed.out', 'subdir-2/']

Filter with functions:

    >>> is_dir = lambda p: p.is_dir()
    >>> is_file = lambda p: p.is_file()
    >>> contains_a = lambda p: "a" in p.name

    >>> list_dir(tmp, filters=(is_dir,))
    ['subdir-1/']

    >>> list_dir(tmp, filters=(is_file,))
    ['bar.md', 'foo.txt']

    >>> list_dir(tmp, filters=(contains_a,))
    ['bar.md']

    >>> list_dir(path(tmp, "subdir-1"), filters=(contains_a,))
    ['baz.bin']

    >>> list_dir(path(tmp, "subdir-1"), filters=(contains_a, is_dir))
    []

Filter with incomplete:

    >>> list_dir(tmp, incomplete="f")
    ['foo.txt']

    >>> list_dir(path(tmp, "subdir-1"), incomplete="b")
    ['baz.bin']

    >>> list_dir(path(tmp, "subdir-1"), incomplete="x")
    []

    >>> list_dir(tmp, incomplete="subdir-1" + os.path.sep)
    ['subdir-1/baz.bin', 'subdir-1/zed.out', 'subdir-1/subdir-2/']

    >>> list_dir(tmp, incomplete=path("subdir-1", "b"))
    ['subdir-1/baz.bin']

    >>> list_dir(tmp, incomplete=path("subdir-1", "s"))
    ['subdir-1/subdir-2/']

Combinations of extension, filters, and incomplete:

    >>> list_dir(tmp, ext=["txt", "md"], filters=[is_file])
    ['bar.md', 'foo.txt']

    >>> list_dir(tmp, ext=["txt", "md"], filters=[is_file], incomplete="b")
    ['bar.md']

    >>> list_dir(tmp, ext=["txt", "md"], filters=[is_file], incomplete="x")
    []
