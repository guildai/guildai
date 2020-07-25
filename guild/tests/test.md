# Guild test support

## Output checked

`guild._test.Py23DocChecker` applies various transformations to "want"
and "got" strings used in doctests.

    >>> from guild._test import Py23DocChecker
    >>> checker = Py23DocChecker()

### Basics

    >>> checker.check_output("1", "1", 0)
    True

    >>> checker.check_output("1", "2", 0)
    False

### Converting unicode "got" on Python 2

Python 2 represents unicode strings as `u'...'`. To normalize strings
across Python versions, we convert such representations to `'...'` by
removing the leading `u`.

Single quote:

    >>> checker._strip_u("u'x'") # doctest: -STRIP_U
    "'x'"

    >>> checker._strip_u("(u'x')") # doctest: -STRIP_U
    "('x')"

Double quote:

    >>> checker._strip_u('u"x"') # doctest: -STRIP_U
    '"x"'

    >>> checker._strip_u('(u"x")') # doctest: -STRIP_U
    '("x")'

Not unicode:

    >>> checker._strip_u("") # doctest: -STRIP_U
    ''

    >>> checker._strip_u("1") # doctest: -STRIP_U
    '1'

    >>> checker._strip_u("'x'") # doctest: -STRIP_U
    "'x'"

    >>> checker._strip_u('"x"') # doctest: -STRIP_U
    '"x"'

    >>> checker._strip_u("('cpu', 'hi')") # doctest: -STRIP_U
    "('cpu', 'hi')"

## Current directory

Guild ensures that the current directory is the test file parent
directory.

    >>> cwd()
    '.../guild/tests'

    >>> dir()
    ['Makefile', ..., 'test.md', ...]

Use `cd` to change directories. This change is reverted when the test
file finishes.

    >>> cd("samples")

    >>> dir()
    ['config', 'opref-runs', 'packages', 'projects', ...]
