# Auto complete

Helper functions:

    >>> def ac_f(cmd, param_name):
    ...     for param in cmd.params:
    ...         if param.name == param_name:
    ...             assert param.autocompletion, (param, cmd)
    ...             def f(**kw):
    ...                 with Env({"_GUILD_COMPLETE": "complete"}):
    ...                     return param.autocompletion(**kw)
    ...             return f
    ...     assert False, (param_name, cmd.params)

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
    view
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

    >>> project = ac_project = Project(sample("projects", "autocomplete"))

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
    ...     ctx.parent = main.main.make_context("", ["-H", project.guild_home])
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
    !!no-colon-wordbreak
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

The list includes a directive to remove the colon from COMP_WORDBREAKS
to support proper expansion for operations that contain colons.

If we specify something for opspec, we get matching ops and
scripts. Scripts are represented by the `!!file` directive, which is
used by the bash completion handlers to find matching files.

    >>> run_ac(run._ac_opspec, [], "echo")
    !!no-colon-wordbreak
    echo
    !!file:*

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

### Path

Paths used for `diff` depend on a number of other arguments:

- Default or explicit runs
- If --sourcecode is specified
- If --working or --working-dir is specified

We return to the autocomplete project and its associated runs.

    >>> project = ac_project

A helper to print path completions:

    >>> def ac_diff_paths(args):
    ...     from guild.commands import main
    ...     ctx = runs_diff.diff_runs.make_context("", list(args))
    ...     ctx.parent = main.main.make_context("", ["-H", project.guild_home])
    ...     with Env({"_GUILD_COMPLETE": "complete"}):
    ...         for path in runs_diff._ac_path(["diff"] + args, ctx):
    ...             print(path)

Paths are resolved using the `!!runfiles` directive. The base dir
differs according to the current set of diff arguments.

The default uses the second-to-last run as the base.

    >>> ac_diff_paths([])
    !!runfiles:...runs/bbb

Specifying a single run to diff isn't a valid command so there are no
completions.

    >>> ac_diff_paths(["aaa"])

When we specify two runs, as required, completions are provided for
the first run.

    >>> ac_diff_paths(["aaa", "bbb"])
    !!runfiles:.../runs/aaa

Working dir is always used as the base dir when specified.

    >>> ac_diff_paths(["--working-dir", "xxx"])
    !!runfiles:xxx

    >>> ac_diff_paths(["--working-dir", "xxx", "aaa"])
    !!runfiles:xxx

    >>> ac_diff_paths(["--working-dir", "xxx", "aaa", "bbb"])
    !!runfiles:xxx

The `--working` option indicates the base is the project drectory.

    >>> ac_diff_paths(["--working"])
    !!runfiles:.../samples/projects/autocomplete/

    >>> ac_diff_paths(["--working", "aaa"])
    !!runfiles:.../samples/projects/autocomplete/

Specifying two runs with `--working` is not valid so we get no
completions.

    >>> ac_diff_paths(["--working", "aaa", "bbb"])

The `--sourcecode` option uses the selected run source code directory.

    >>> ac_diff_paths(["--sourcecode"])
    !!runfiles:.../runs/bbb/.guild/sourcecode

Specifying a single run is not value.

    >>> ac_diff_paths(["--sourcecode", "aaa"])

    >>> ac_diff_paths(["--sourcecode", "aaa", "bbb"])
    !!runfiles:.../runs/aaa/.guild/sourcecode

## `operations`

Completion for `operations` is provided by
`guild.commands.operations`.

    >>> from guild.commands import operations

`_ac_operation` resolves available operations, which are applied as
filters.

We use the `optimizers` project to illustrate.

    >>> project = Project(sample("projects", "optimizers"))

Helper to print completions:

    >>> def ops_ac(incomplete):
    ...     ctx = operations.operations.make_context("", [])
    ...     with SetCwd(project.cwd):
    ...         for op in operations._ac_operation(ctx, incomplete):
    ...             print(op)

Empty incomplete:

    >>> ops_ac("")
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

Various incompletes:

    >>> ops_ac("opt-")
    opt-test-1
    opt-test-2
    opt-test-3
    opt-test-4

    >>> ops_ac("x")

## `export`

The `export` command changes the default behavior to support directory
completion for the `runs` argument. This is because the `export`
command requires a location argument as the last of many potential
arguments. Preceding arguments are used for `runs`.

It's far more common to use `guild export <export-dir>` than to
include runs. The default click completion logic treats `<export-dir>`
in this case as a run, which is a reasonable assumption since it
doesn't know if it's the last argument that will be provided.

To show the behavior, we examine the `runs` param for the applicable
command function.

    >>> from guild.commands import runs_export
    >>> runs_export.export_runs.params[0].name
    'runs'

When executed, the auto completion function uses the `!!dir` directive
to resolve directory locations.

    >>> with Env({"_GUILD_COMPLETE": "complete"}):
    ...     runs_export.export_runs.params[0].autocompletion()
    ['!!dir']

In this case it's not possible to support run completion.

## `help`

Help completion supports lookup of installed Guild packages and
directories.

    >>> from guild.commands import help

    >>> with Env({"_GUILD_COMPLETE": "complete"}):
    ...     help._ac_path_or_package("")
    [...'!!dir']

## `import`

`import` uses the same scheme as `export` (see above).

    >>> from guild.commands import runs_import
    >>> runs_import.import_runs.params[0].name
    'runs'

The archive location for import is a directory.

    >>> with Env({"_GUILD_COMPLETE": "complete"}):
    ...     runs_import.import_runs.params[0].autocompletion()
    ['!!dir']

## `init`

    >>> from guild.commands import init

Helper to print completions.

    >>> def ac_init(f, incomplete=""):
    ...     from guild.commands import main
    ...     ctx = init.init.make_context("", [])
    ...     ctx.parent = main.main.make_context("", ["-H", project.guild_home])
    ...     with Env({"_GUILD_COMPLETE": "complete"}):
    ...         for val in f(ctx=ctx, incomplete=incomplete):
    ...             print(val)

Python versions:

    >>> ac_f(init.init, "python")()
    ['!!command:python*[^-config]']

Target dir:

    >>> ac_f(init.init, "dir")()
    ['!!dir']

Guild version or path:

    >>> ac_init(init._ac_guild_version_or_path)
    0.1.0
    ...
    0.7.0
    ...
    !!file:*.@(whl)

Guild home:

    >>> ac_init(init._ac_guild_home)
    !!dir

Requirements:

    >>> ac_init(init._ac_requirement)
    !!file:*.@(txt)

Additional Python path:

    >>> ac_init(init._ac_path)
    !!dir
