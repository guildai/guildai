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
    ...         for val in check._ac_all_tests(incomplete):
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

## Runs Support

Auto completion support for run-specific commands is provided by
`guild.commands.runs_support`.

    >>> from guild.commands import runs_support

With the exception of `-S, --started`, each filter that accepts a
value supports auto completion. These include:

 - `-o, --operation`
 - `-l, --label`
 - `-d, --digest`

In addition, the `RUN` arguments support autocompletion of applicable
run IDs. Filters are applied to limit the available run IDs in auto
complete.

To illustate the various auto completion scenarions, we generate a
number of runs.

    >>> project = Project(sample("projects", "autocomplete"))

    >>> project.run("a", run_dir=path(project.guild_home, "runs", "aaa"))
    a
    >>> project.run("b", run_dir=path(project.guild_home, "runs", "bbb"))
    b
    >>> project.run("c", run_dir=path(project.guild_home, "runs", "ccc"))
    c

A helper to show completions:

    >>> def cmd_ac(cmd, ac_f, args, incomplete):
    ...     from guild.commands import main
    ...     ctx = cmd.make_context("", args, resilient_parsing=True)
    ...     ctx.parent = main.main.make_context("", ["-H", project.guild_home])
    ...     for val in ac_f(ctx=ctx, incomplete=incomplete):
    ...         print(val)

We need a command to parse arguments. We use `cat`, which supports all
of the run filters and accepts a RUN arg.

    >>> from guild.commands import cat

Runs for no args:

    >>> cmd_ac(cat.cat, runs_support._ac_run, [], "")
    aaa
    bbb
    ccc

Ops for no args:

    >>> cmd_ac(cat.cat, runs_support._ac_operation, [], "")
    a
    b
    c

Labels for no args:

    >>> cmd_ac(cat.cat, runs_support._ac_label, [], "")
    "msg=a"
    "msg=b"
    "msg=c"

Labels for incomplete:

    >>> cmd_ac(cat.cat, runs_support._ac_label, [], "a")

Digests for no args:

    >>> cmd_ac(cat.cat, runs_support._ac_digest, [], "")
    0fc1636e7d3653be41f89833776cdb8b

Runs for incomplete:

    >>> cmd_ac(cat.cat, runs_support._ac_run, [], "a")
    aaa

    >>> cmd_ac(cat.cat, runs_support._ac_run, [], "bb")
    bbb

Runs for ops:

    >>> cmd_ac(cat.cat, runs_support._ac_run, ["-o", "a"], "")
    aaa

    >>> cmd_ac(cat.cat, runs_support._ac_run, ["-o", "a", "-o", "c"], "")
    aaa
    ccc
