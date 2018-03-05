# Plugin utils

The `guild.plugin_util` module provides some helper functions for
plugins.

    >>> from guild import plugin_util

## Converting plugin args to flags

Use `args_to_flags` to convert a list of command line args to flag
keyvals.

    >>> a2f = plugin_util.args_to_flags

    >>> a2f([])
    {}

    >>> a2f(["--foo", "123"])
    {'foo': 123}

    >>> pprint(a2f(["--foo", "123", "--bar", "hello"]))
    {'bar': 'hello', 'foo': 123}

Options without values are treated as True:

    >>> a2f(["--foo"])
    {'foo': True}

    >>> pprint(a2f(["--foo", "--bar", "1.123"]))
    {'bar': 1.123, 'foo': True}

Short form arguments are supported:

    >>> a2f(["-a", "bar"])
    {'a': 'bar'}

    >>> a2f(["-abar"])
    {'a': 'bar'}

If multipe option args are specified, only the last is used:

    >>> a2f(["--foo", "abd", "def"])
    {'foo': 'def'}
