# Auto complete

## Init

Context manager to set completions for zsh.

    >>> def BashCompletion():
    ...     return Env({"_GUILD_COMPLETE": "complete", "_GUILD_COMPLETE_SHELL": "bash"})

    >>> from guild.commands.ac_support import _active_shell
    >>> with BashCompletion():
    ...     _active_shell()
    'bash'

Helper functions:

    >>> def ac_f(cmd, param_name):
    ...     for param in cmd.params:
    ...         if param.name == param_name:
    ...             assert param.shell_complete, (param, cmd)
    ...             def f(**kw):
    ...                 with BashCompletion():
    ...                     completion_result = param.shell_complete(param, "")
    ...                     completion_result = [
    ...                         result.value if hasattr(result, "value") else result
    ...                         for result in completion_result
    ...                     ]
    ...                     return completion_result
    ...             return f
    ...     assert False, (param_name, cmd.params)

## `check`

    >>> from guild.commands import check

### Tests

Autocomplete shows built-in tests and markdown files.

A helper to show completions.

    >>> def ac_check_tests(incomplete, subdir=""):
    ...     ctx = check.check.make_context("", [])
    ...     with BashCompletion():
    ...         for val in check._ac_all_tests(ctx, None, incomplete):
    ...             print(val)

Default list includes all built-in tests and a directive to include
markdown and text files.

    >>> ac_check_tests("")
    additional-deps
    anonymous-models
    api
    api-cmd
    autocomplete-bash
    autocomplete-zsh
    ...
    var
    vcs-source
    vcs-utils
    view
    yaml-utils
    !!file:*.@(md|txt)

Providing a prefix limits the tests shown.

    >>> ac_check_tests("run")
    run-attrs
    run-files
    run-impl
    run-labels
    run-manifest
    run-merge
    run-ops
    run-output
    run-scripts
    run-status
    run-stop
    run-stop-after
    run-utils
    run-with-proto
    runs-1
    runs-2
    !!file:*.@(md|txt)

## Runs Init

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

    >>> def cmd_ac(cmd, param_name, args, incomplete=""):
    ...     from guild.commands import main
    ...     ac_f = None
    ...     param_opt = None
    ...     for param in cmd.params:
    ...         if param.name == param_name:
    ...             assert param.shell_complete, param.name
    ...             ac_f = param.shell_complete
    ...             param_opt = param.opts[0]
    ...             break
    ...     assert ac_f, param_name
    ...     assert param_opt, param_name
    ...     ctx = cmd.make_context(cmd.name, list(args), resilient_parsing=True)
    ...     ctx.parent = main.main.make_context("guild", ["-H", project.guild_home])
    ...     ac_args = [cmd.name] + args
    ...     if param_opt[0] == "-":
    ...         ac_args.append(param_opt)  # simulate the actual partial args for ac
    ...     empty = True
    ...     with BashCompletion():
    ...         with Chdir(project.cwd):
    ...             for val in ac_f(ctx, incomplete):
    ...                 print(val.value if hasattr(val, "value") else val)
    ...                 empty = False
    ...     if empty:
    ...         print("<empty>")


## Completions for `cat`

    >>> from guild.commands import cat

### `cat` run arg

Run completion for no args:

    >>> cmd_ac(cat.cat, "run", [])
    aaa
    bbb
    ccc

Run completion with incomplete"

    >>> cmd_ac(cat.cat, "run", [], "a")
    aaa

Run completion with run arg:

    >>> cmd_ac(cat.cat, "run", ["a"])
    aaa

Run completion with op filter:

    >>> cmd_ac(cat.cat, "run", ["-Fo", "a"])
    aaa

Run completion with no possible matching runs:

    >>> cmd_ac(cat.cat, "run", ["aaabbbccc"])
    <empty>

### `cat` path

Path completions for no args:

    >>> cmd_ac(cat.cat, "path", [])
    !!runfiles:.../runs/ccc

Path completions for a run arg:

    >>> cmd_ac(cat.cat, "path", ["bbb"])
    !!runfiles:.../runs/bbb

Path completions using an operation filter:

    >>> cmd_ac(cat.cat, "path", ["-Fo", "a"])
    !!runfiles:.../runs/aaa

Path completion with `--sourcecode` option:

    >>> cmd_ac(cat.cat, "path", ["-Fo", "b", "--sourcecode"])
    !!runfiles:.../runs/bbb/.guild/sourcecode

### `cat` label

Labels for no args:

    >>> cmd_ac(cat.cat, "filter_labels", [])
    "msg=a"
    "msg=b"
    "msg=c"

Labels for incomplete:

    >>> cmd_ac(cat.cat, "filter_labels", [], "msg=")
    "msg=a"
    "msg=b"
    "msg=c"

    >>> cmd_ac(cat.cat, "filter_labels", [], "msg=c")
    "msg=c"

Labels for operation filter:

    >>> cmd_ac(cat.cat, "filter_labels", ["-Fo", "a", "-Fo", "b"])
    "msg=a"
    "msg=b"

### `cat` digest

Digests for no args:

    >>> cmd_ac(cat.cat, "filter_digest", [])
    44e4e89b8b83aa85d48c3bab1948cd00

    >>> cmd_ac(cat.cat, "filter_digest", [], incomplete="a")
    <empty>

## Completions for `ls`

    >>> from guild.commands import ls

### `ls` run arg

Runs completion for no args:

    >>> cmd_ac(ls.ls, "run", [])
    aaa
    bbb
    ccc

Run completion for run arg:

    >>> cmd_ac(ls.ls, "run", ["cc"])
    ccc

Run completion for incomplete:

    >>> cmd_ac(ls.ls, "run", [], "a")
    aaa

Run completion for no matching runs:

    >>> cmd_ac(ls.ls, "run", [], "z")
    <empty>

### `ls` path

Path completion for no args:

    >>> cmd_ac(ls.ls, "path", [])
    !!runfiles:.../runs/ccc

Path completion for valid run arg:

    >>> cmd_ac(ls.ls, "path", ["2"])
    !!runfiles:.../runs/bbb

Path completion for `--sourcecode` option.

    >>> cmd_ac(ls.ls, "path", ["--sourcecode"])
    !!runfiles:.../runs/ccc/.guild/sourcecode

## Completions for `diff`

    >>> from guild.commands import diff

### `run` arg

    >>> cmd_ac(diff.diff, "run", [])
    aaa
    bbb
    ccc

### `other_run` arg

    >>> cmd_ac(diff.diff, "other_run", [])
    aaa
    bbb
    ccc

### `paths` args

No args - completes paths for latest run:

    >>> cmd_ac(diff.diff, "paths", [])
    !!runfiles:.../runs/ccc

A run is specified:

    >>> cmd_ac(diff.diff, "paths", ["2"])
    !!runfiles:.../runs/bbb

The first run is used for completions when two runs are specified.

    >>> cmd_ac(diff.diff, "paths", ["aaa", "bbb"])
    !!runfiles:.../runs/aaa

Source code paths:

    >>> cmd_ac(diff.diff, "paths", ["--sourcecode"])
    !!runfiles:.../runs/ccc/.guild/sourcecode

    >>> cmd_ac(diff.diff, "paths", ["b", "--sourcecode"])
    !!runfiles:.../bbb/.guild/sourcecode

    >>> cmd_ac(diff.diff, "paths", ["--sourcecode", "b"])
    !!runfiles:.../bbb/.guild/sourcecode

    >>> cmd_ac(diff.diff, "paths", ["aaa", "bbb", "--sourcecode"])
    !!runfiles:.../runs/aaa/.guild/sourcecode

Path completion with `--working` refers to project path:

    >>> cmd_ac(diff.diff, "paths", ["--working"])
    !!runfiles:.../samples/projects/autocomplete/

    >>> cmd_ac(diff.diff, "paths", ["--working", "-Fo", "a"])
    !!runfiles:.../samples/projects/autocomplete/

    >>> cmd_ac(diff.diff, "paths", ["--working", "aaa", "bbb"])
    !!runfiles:.../samples/projects/autocomplete/

Completions with `--dir` refer to the specified dir:

    >>> cmd_ac(diff.diff, "paths", ["--dir", "foo"])
    !!runfiles:.../samples/projects/autocomplete/foo

Various other options that don't work with path:

    >>> cmd_ac(diff.diff, "paths", ["--env", "a"])
    <empty>

    >>> cmd_ac(diff.diff, "paths", ["--flags", "c"])
    <empty>

    >>> cmd_ac(diff.diff, "paths", ["--attrs"])
    <empty>

    >>> cmd_ac(diff.diff, "paths", ["--deps"])
    <empty>

### `dir` arg

    >>> cmd_ac(diff.diff, "dir", [])
    !!dir

### `cmd` arg

    >>> cmd_ac(diff.diff, "cmd", [])
    !!command

## Completions for `run`

Autocomplete support for the run command is provided by `_ac_xxx`
function in `guild.commands.run`.

    >>> from guild.commands import run

We use the `optimizers` project to illustrate.

    >>> project = Project(sample("projects", "optimizers"))

A helper to show completions:

    >>> def run_ac(param_name, args, incomplete=""):
    ...     with Chdir(project.cwd):
    ...         cmd_ac(run.run, param_name, args, incomplete)

### Op spec

An op spec can be either an available operation or a supported
runnable file. Guild currently supports two runnable file types:

- Python files (*.py)
- Jupyter notebooks (*.ipynb)

Runnable files are represented by the `!!file` directive, which is
used by the bash completion handlers to find matching files.

    >>> run_ac("opspec", [])
    !!no-colon-wordbreak
    echo
    fail
    flags
    noisy
    noisy-flubber
    opt-test-1
    opt-test-2
    opt-test-3
    opt-test-4
    poly
    tune-echo
    tune-echo-2
    !!file:*.@(py|ipynb)

The list includes a directive to remove the colon from COMP_WORDBREAKS
to support proper expansion for operations that contain colons.

If we specify something for opspec, we get matching ops and scripts.

    >>> run_ac("opspec", [], "ech")
    !!no-colon-wordbreak
    echo
    !!file:*.@(py|ipynb)

### Flags

All flag completions contain a `!!nospace` directive to allow the user
to enter a value for flag after the equals sign.

If a project has a default operation, flags are listed for it.

    >>> run_ac("flags", [])
    noise=
    x=
    !!nospace

With incomplete:

    >>> run_ac("flags", [], "x")
    x=
    !!nospace

Provide an explicit operation.

    >>> run_ac("flags", ["echo"])
    x=
    y=
    z=
    !!nospace

When choices are available, they are shown once the flag is
identified.

    >>> run_ac("flags", ["echo"], "z=")
    a
    b
    c
    d

    >>> run_ac("flags", ["flags"], "c=")
    123
    1.123
    hello
    false

Choices are limited as well.

    >>> run_ac("flags", ["echo"], "z=d")
    d

    >>> run_ac("flags", ["flags"], "c=hel")
    hello

If there are no sensible choices to present, completions are empty.

    >>> run_ac("flags", ["flags"], "nt=")
    <empty>

Flag type is otherwise used to provide possible completions.

Types that don't support completion include int, float and number.

    >>> run_ac("flags", ["flags"], "i=")
    <empty>

    >>> run_ac("flags", ["flags"], "f=")
    <empty>

    >>> run_ac("flags", ["flags"], "n=")
    <empty>

Boolean flags support 'true' and 'false'.

    >>> run_ac("flags", ["flags"], "b=")
    true
    false

    >>> run_ac("flags", ["flags"], "b=t")
    true

Paths support file name completions.

    >>> run_ac("flags", ["flags"], "p=")
    !!file:*

    >>> run_ac("flags", ["flags"], "ep=")
    !!file:*

String types do not.

    >>> run_ac("flags", ["flags"], "s=")
    <empty>


If a flag starts with '@' it's considered a batch file. In this case
completion is handled by the `!!batchfile` directive.

    >>> run_ac("flags", ["echo"], "@")
    !!batchfile:*.@(csv|yaml|yml|json)

Flag type

## Completions `operations`

    >>> from guild.commands import operations

### Filter arg

Default:

    >>> cmd_ac(operations.operations, "filters", [])
    echo
    fail
    flags
    noisy
    noisy-flubber
    opt-test-1
    opt-test-2
    opt-test-3
    opt-test-4
    poly
    tune-echo
    tune-echo-2

Filters limit ops:

    >>> cmd_ac(operations.operations, "filters", ["opt-"])
    opt-test-1
    opt-test-2
    opt-test-3
    opt-test-4

As do incomplets:

    >>> cmd_ac(operations.operations, "filters", [], "opt-")
    opt-test-1
    opt-test-2
    opt-test-3
    opt-test-4

    >>> cmd_ac(operations.operations, "filters", [], "x")
    <empty>

## `export`

The first param to export is the export location.

    >>> from guild.commands import runs_export
    >>> runs_export.export_runs.params[0].name
    'location'

Locations may be directories or zip files.

    >>> with BashCompletion():
    ...     [_.value for _ in runs_export.export_runs.params[0].shell_complete(None, "")]
    ['!!dir', '!!file:*.@(zip)']

## `help`

Help completion supports lookup of installed Guild packages and
directories.

    >>> from guild.commands import help

    >>> with BashCompletion():
    ...     help._ac_path_or_package(None, None, "")
    [...'!!dir']

## `import`

`import` uses the same scheme as `export` (see above).

    >>> from guild.commands import runs_import
    >>> runs_import.import_runs.params[0].name
    'archive'

The archive location for import is a directory.

    >>> with BashCompletion():
    ...     [_.value for _ in runs_import.import_runs.params[0].shell_complete(None, "")]
    ['!!dir', '!!file:*.@(zip)']

## `init`

    >>> from guild.commands import init

Helper to print completions.

    >>> def ac_init(f, incomplete=""):
    ...     from guild.commands import main
    ...     ctx = init.init.make_context("", [])
    ...     ctx.parent = main.main.make_context("", ["-H", project.guild_home])
    ...     with BashCompletion():
    ...         for val in f(ctx, None, incomplete):
    ...             print(val.value if hasattr(val, "value") else val)

Python versions:

    >>> ac_f(init.init, "python")()
    ['!!command:python*[^-config]']

Target dir:

    >>> ac_f(init.init, "dir")()
    ['!!dir']

Guild version or path:

    >>> ac_init(init._ac_guild_version_or_path)
    ???!!file:*.@(whl)

Guild home:

    >>> ac_init(init._ac_guild_home)
    !!dir

Requirements:

    >>> ac_init(init._ac_requirement)
    !!file:*.@(txt)

Additional Python path:

    >>> ac_init(init._ac_dir)
    !!dir
