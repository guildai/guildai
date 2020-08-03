# Auto complete

## `check`

    >>> from guild.commands import check

### Tests

Autocomplete shows built-in tests and markdown files.

Here's a sample directory.

    >>> tmp = mkdtemp()
    >>> mkdir(path(tmp, "subdir_1"))
    >>> mkdir(path(tmp, "subdir_2"))
    >>> touch(path(tmp, "TESTS.md"))
    >>> touch(path(tmp, "subdir_1", "TESTS_2.md"))

And a helper to show completions.

    >>> def ac_check_tests(incomplete, subdir=""):
    ...     with Chdir(path(tmp, subdir)):
    ...         for val in check._ac_all_tests(None, None, incomplete):
    ...             print(val)

Default list includes all built-in tests, local dirs, and markdown files.

    >>> ac_check_tests("")
    anonymous-models
    api
    autocomplete
    ...
    var
    vcs-utils
    subdir_1/
    subdir_2/
    TESTS.md

Providing a prefix limits the tests shown.

    >>> ac_check_tests("run")
    run-files
    run-impl
    run-labels
    run-ops
    run-output
    run-scripts
    run-stop-after
    run-utils
    run-with-proto
    runs-1
    runs-2

Providing a file prefix limits to the matchin files.

    >>> ac_check_tests("TES")
    TESTS.md

Specifying a subdirectory lists only files as built-ins no longer
match.

    >>> ac_check_tests("subdir_1/")
    subdir_1/TESTS_2.md

Nothin matches under `subdir_2`.

    >>> ac_check_tests("subdir_2/")
