# Whitelisting Code

This set of tests addresses false positives when running
[Vulture](https://github.com/jendrikseipp/vulture) on the Guild code
base. It contains explicit usage of code otherwise not used, untested,
or simply missed by Vulture.

It's organized by module and tested code.

`guild/_api.py: unused attribute 'cmd_cwd'`

    >>> from guild._api import RunError
    >>> err = RunError((1, 2, 3), 4, 5)
    >>> err.cmd_args
    1

    >>> err.cmd_cwd
    2

    >>> err.cmd_env
    3

    >>> err.returncode
    4

    >>> err.output
    5

`guild/_test.py: unused attribute '_OPTION_DIRECTIVE_RE'`

    >>> import doctest
    >>> doctest.DocTestParser()._OPTION_DIRECTIVE_RE  # doctest: -NORMALIZE_PATHS
    re.compile('#\\s*doctest:\\s*([^\\n\\\'"]*)$', re.MULTILINE)

`guild/_test.py:477: unused method '_parse_example'`

    >>> doctest.DocTestParser()._parse_example
    <bound method DocTestParser._parse_example ...>
