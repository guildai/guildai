# Index 2

The module `guild.index2` is the second generation run index, which
uses SQLite and stores more information than the first generation
index.

    >>> from guild import index2 as indexlib

We can create an index in a directory:

    >>> tmp_dir = mkdtemp()
    >>> index = indexlib.RunIndex(tmp_dir)

When instantiated, the index generates these files:

    >>> dir(tmp_dir)
    ['index_v1.db']
