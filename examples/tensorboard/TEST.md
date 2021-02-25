# TensorBoard Example

## Nested TF Event Files and Scalars

    >>> run("guild run nested.py -y")
    <exit 0>

    >>> run("guild runs info")
    id: ...
    operation: nested.py
    ...
    scalars:
      foo#a: 2.000000 (step 2)
      foo/bar#a: 4.000000 (step 4)
      foo/bar/baz#a: 6.000000 (step 6)
    <exit 0>
