# CLI Tests

    >>> from guild import cli

## Wrapping Text

    >>> print(cli.wrap(""))

    >>> print(cli.wrap("a b c", 1))
    a
    b
    c

    >>> print(cli.wrap("a b c", 2))
    a
    b
    c

    >>> print(cli.wrap("a b c", 3))
    a b
    c

    >>> print(cli.wrap("a b c", 4))
    a b
    c

    >>> print(cli.wrap("a b c", 5))
    a b c
