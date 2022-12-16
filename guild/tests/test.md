# Guild test support

## Test output cheker

`guild._test.Py23DocChecker` applies various transformations to "want"
and "got" strings used in doctests.

    >>> from guild._test import Checker
    >>> checker = Checker()

Helper function to test *want* vs *got* with option flags:

    >>> def check(want, got, optionflags=0):
    ...     return checker.check_output(want, got, optionflags)

Provide checker options, defined in `guild._test` under `opts`
namespace.

    >>> from guild import _test as opts

Provide access to `doctest` options.

    >>> import doctest

### Basics

    >>> check("1", "1")
    True

    >>> check("1", "2")
    False

    >>> check("1...", "1", doctest.ELLIPSIS)
    True

    >>> check("...", "1", doctest.ELLIPSIS)
    True

### Checker transformation options

Stript ANSI format codes from 'got':

    >>> check("hello", "\x1b[31mhello\x1b[0m")
    False

    >>> check("hello", "\x1b[31mhello\x1b[0m", opts.STRIP_ANSI_FMT)
    True

Normalize paths for Windows:

    >>> with Platform("Windows"):
    ...     check("/foo/bar", "\\foo\\bar")
    False

    >>> with Platform("Windows"):
    ...     check("/foo/bar", "\\foo\\bar", opts.NORMALIZE_PATHS)
    True

    >>> with Platform("SomeOtherPlatform"):
    ...     check("/foo/bar", "\\foo\\bar", opts.NORMALIZE_PATHS)
    False

Alternative leading wildcard:

    >>> check("???", "1")
    False

    >>> check("???", "1", doctest.ELLIPSIS)
    True

    >>> check("1???", "1", doctest.ELLIPSIS)
    False

    >>> check("1...", "1", doctest.ELLIPSIS)
    True

Using `STRICT` with other transform options to disable those options.

    >>> check("hello", "\x1b[31mhello\x1b[0m", opts.STRIP_ANSI_FMT | opts.STRICT)
    False

    >>> with Platform("Windows"):
    ...     check("/foo/bar", "\\foo\\bar", opts.NORMALIZE_PATHS | opts.STRICT)
    False

    >>> check("???", "1", doctest.ELLIPSIS | opts.STRICT)
    False


## Current directory when running a test

Guild ensures that the current directory is the test file parent
directory.

    >>> cd(tests_dir())

    >>> cwd()
    '.../guild/tests'

    >>> dir()
    ???'Makefile', ..., 'test.md', ...]

Use `cd` to change directories. This change is reverted when the test
file finishes.

    >>> cd("samples")

    >>> pprint(dir())  # doctest: +REPORT_UDIFF
    ['config',
     'filter-runs',
     'opref-runs',
     'packages',
     'projects',
     'runs',
     'scripts',
     'select-files',
     'serve',
     'templates',
     'textorbinary']

## Ignoring output

    >>> with Ignore(["hello", "bye", "some .+ message"]):
    ...     print("foo")
    ...     print("bar")
    ...     print("hello")
    ...     print("some xxx message")
    foo
    bar

## Exit 0

Output from `run()` ends with `<exit STATUS>` where `STATUS` is the
exit status code from the command process. In cases where the exit
status code is `0`, we can omit the asserted exit code for brevity.

We simulate the exit code output by printing it directly.

    >>> print("""Sample output - line 1
    ... Sample outout - line 2
    ... <exit 0>""")
    Sample output - line 1
    Sample outout - line 2

We can also include the exit status.

    >>> print("""Sample output - line 1
    ... Sample outout - line 2
    ... <exit 0>""")
    Sample output - line 1
    Sample outout - line 2
    <exit 0>
