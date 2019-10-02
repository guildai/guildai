# Op Utils

    >>> from guild import op_util2 as op_util

## Split batch file from args

    >>> op_util.split_batch_files([
    ...     "foo",
    ...     "@file-1",
    ...     "bar=123",
    ...     "@file-2",
    ... ])
    (['file-1', 'file-2'], ['foo', 'bar=123'])
