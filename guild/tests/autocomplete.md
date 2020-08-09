# Auto complete

## `check`

    >>> from guild.commands import check

### Tests

Autocomplete shows built-in tests and markdown files.

A helper to show completions.

    >>> def ac_check_tests(incomplete, subdir=""):
    ...     ctx = check.check.make_context("", [])
    ...     with Env({"_GUILD_COMPLETE": "complete"}):
    ...         for val in check._ac_all_tests(incomplete, ctx):
    ...             print(val)

Default list includes all built-in tests and a directive to include
markdown and text files.

    >>> ac_check_tests("")
    anonymous-models
    api
    autocomplete
    ...
    var
    vcs-utils
    !!file:*.@(md|txt)

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
    !!file:*.@(md|txt)

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
    ...     with Env({"_GUILD_COMPLETE": "complete"}):
    ...         for val in ac_f(ctx=ctx, incomplete=incomplete):
    ...             print(val)

We need a command to parse arguments. We use `cat`, which supports all
of the run filters and accepts a RUN arg.

    >>> from guild.commands import cat

### Run completion

Runs for no args:

    >>> cmd_ac(cat.cat, runs_support.ac_run, [], "")
    aaa
    bbb
    ccc

Runs for incomplete:

    >>> cmd_ac(cat.cat, runs_support.ac_run, [], "a")
    aaa

    >>> cmd_ac(cat.cat, runs_support.ac_run, [], "bb")
    bbb

Runs for ops:

    >>> cmd_ac(cat.cat, runs_support.ac_run, ["-o", "a"], "")
    aaa

    >>> cmd_ac(cat.cat, runs_support.ac_run, ["-o", "a", "-o", "c"], "")
    aaa
    ccc

### Operation completion

Ops for no args:

    >>> cmd_ac(cat.cat, runs_support.ac_operation, [], "")
    a
    b
    c

### Label completion

Labels for no args:

    >>> cmd_ac(cat.cat, runs_support.ac_label, [], "")
    "msg=a"
    "msg=b"
    "msg=c"

Labels for incomplete:

    >>> cmd_ac(cat.cat, runs_support.ac_label, [], "a")

### Digest completion

Digests for no args:

    >>> cmd_ac(cat.cat, runs_support.ac_digest, [], "")
    0fc1636e7d3653be41f89833776cdb8b

### Path completion

Note that cat.cat only uses `ac_run_filepath` but we use it to verify
support for `ac_run_dirpath` as a convenience. Both completion
functions can be tested this way.

    >>> cmd_ac(cat.cat, runs_support.ac_run_filepath, [], "")
    !!runfiles:.../runs/ccc

    >>> cmd_ac(cat.cat, runs_support.ac_run_dirpath, [], "")
    !!rundirs:.../runs/ccc

## `run`

Autocomplete support for the run command is provided by `_ac_xxx`
function in `guild.commands.run`.

    >>> from guild.commands import run

We use the `optimizers` project to illustrate.

    >>> project = Project(sample("projects", "optimizers"))

A helper to show completions:

    >>> def run_ac(ac_f, args, incomplete):
    ...     from guild.commands import main
    ...     ctx = run.run.make_context("", args, resilient_parsing=True)
    ...     with Env({"_GUILD_COMPLETE": "complete"}):
    ...         with Chdir(project.cwd):
    ...             for val in ac_f(ctx=ctx, incomplete=incomplete):
    ...                 print(val)


### Op spec

Op spec completion is handled by `_ac_opspec`.

An op spec can be either an available operation or a Python script.

If we don't specify anything for opspec we get the list of defined
operations.

    >>> run_ac(run._ac_opspec, [], "")
    echo
    fail
    noisy
    noisy-flubber
    opt-test-1
    opt-test-2
    opt-test-3
    opt-test-4
    poly
    tune-echo
    tune-echo-2

If we specify something for opspec, we get matching ops and
scripts. Scripts are represented by the `!!file` directive, which is
used by the bash completion handlers to find matching files.

    >>> run_ac(run._ac_opspec, [], "echo")
    echo
    !!file:*.@(py)

### Flags

Flag completion is handled by `_ac_flag`. All flag completions contain
a `!!nospace` directive to allow the user to enter a value for flag
after the equals sign.

If a project has a default operation, flags are listed for it.

    >>> run_ac(run._ac_flag, [], "")
    noise=
    x=
    !!nospace

Provide an explicit operation.

    >>> run_ac(run._ac_flag, ["echo"], "")
    x=
    y=
    z=
    !!nospace

Incomplete values limit the completions.

    >>> run_ac(run._ac_flag, ["echo"], "x")
    x=
    !!nospace

When choices are available, they are shown once the flag is
identified.

    >>> run_ac(run._ac_flag, ["echo"], "z=")
    a
    b
    c
    d

Choices are limited as well.

    >>> run_ac(run._ac_flag, ["echo"], "z=d")
    d

If a flag starts with '@' it's considered a batch file. In this case
completion is handled by the `!!batchfile` directive.

    >>> run_ac(run._ac_flag, ["echo"], "@")
    !!batchfile:*.@(csv|yaml|yml|json)

## `diff`

Auto completion for the `diff` command is handled by
`guild.commands.runs_diff`.

    >>> from guild.commands import runs_diff

### Diff program

The diff program is resolved using a `!!command` directive.

    >>> ctx = runs_diff.diff_runs.make_context("", [])
    >>> with Env({"_GUILD_COMPLETE": "complete"}):
    ...     print(runs_diff._ac_cmd(ctx))
    ['!!command']


Autocomplete for `ls` is implemented by `guild.commands.ls`.

    >>> from guild.commands import ls

We generate a run to test.

    >>> project = Project(sample("projects", "autocomplete"))
    >>> project.run("a")
    a

### Path

Paths use the `!!rundirs` directive to provide completions for the
applicable run directory.

    >>> with SetGuildHome(project.guild_home):
    ...     ctx = ls.ls.make_context("", [])
    ...     with Env({"_GUILD_COMPLETE": "complete",
    ...               "_GUILD_COMPLETE_DEBUG": "1"}):
    ...         ls._ac_path(ctx=ctx)
    ['!!rundirs:.../runs/...']
