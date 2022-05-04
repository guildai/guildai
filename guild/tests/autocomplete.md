# Auto complete

Helper functions:

    >>> def ac_f(cmd, param_name):
    ...     for param in cmd.params:
    ...         if param.name == param_name:
    ...             assert param.shell_complete, (param, cmd)
    ...             def f(**kw):
    ...                 with Env({"_GUILD_COMPLETE": "complete"}):
    ...                     completion_result = param.shell_complete(param, "")
    ...                     if completion_result and hasattr(completion_result, "value"):
    ...                         completion_result = [_.value for _ in completion_result]
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
    ...     with Env({"_GUILD_COMPLETE": "complete"}):
    ...         for val in check._ac_all_tests(incomplete, ctx):
    ...             print(val)

Default list includes all built-in tests and a directive to include
markdown and text files.

    >>> ac_check_tests("")
    additional-deps
    anonymous-models
    api
    api-cmd
    autocomplete
    ...
    var
    vcs-source
    vcs-utils
    view
    yaml-utils
    additional-deps.md
    anonymous-models.md
    ...
    requirements.txt
    ...
    view.md
    yaml-utils.md

Providing a prefix limits the tests shown.

    >>> ac_check_tests("run")
    run-attrs
    run-files
    run-impl
    run-labels
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
    run-attrs.md
    run-files.md
    run-impl.md
    run-labels.md
    run-ops.md
    run-output.md
    run-scripts.md
    run-status.md
    run-stop-after.md
    run-stop.md
    run-utils.md
    run-with-proto.md
    runs-1.md
    runs-2.md

## Runs Init

To illustate the various auto completion scenarions, we generate a
number of runs.

    >>> project = ac_project = Project(sample("projects", "autocomplete"))

    >>> project.run("a", run_dir=path(project.guild_home, "runs", "aaa"))
    a
    >>> project.run("b", run_dir=path(project.guild_home, "runs", "bbb"))
    b
    >>> project.run("c", run_dir=path(project.guild_home, "runs", "ccc"))
    c

We also add a few files manually to validate that the directory listing
is working correctly

    >>> for run in project.list_runs():
    ...     run_dir = os.path.dirname(run.guild_path())
    ...     fname = os.path.basename(run_dir) + "-file"
    ...     os.makedirs(os.path.join(run_dir, "foo"), exist_ok=True)
    ...     with open(os.path.join(run_dir, fname), "w") as f:
    ...         _ = f.write("something")
    ...     with open(os.path.join(run_dir, ".guild", "sourcecode", fname+".py"), "w") as f:
    ...         _ = f.write("something")
    ...     os.makedirs(os.path.join(run_dir, ".guild", "sourcecode", "inner_source"))
    ...     with open(os.path.join(run_dir, ".guild", "sourcecode", "inner_source", "inner_"+fname+".py"), "w") as f:
    ...         _ = f.write("something")
    ...     with open(os.path.join(run_dir, "foo", fname+".py"), "w") as f:
    ...         _ = f.write("something")

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
    ...     # set this so that our paths are absolute, which we use to verify correctness
    ...     ctx.params["abspath"] = True
    ...     ac_args = [cmd.name] + args
    ...     if param_opt[0] == "-":
    ...         ac_args.append(param_opt)  # simulate the actual partial args for ac
    ...     empty = True
    ...     with Env({"_GUILD_COMPLETE": "complete"}):
    ...         for val in ac_f(ctx, incomplete):
    ...             print(val.value if hasattr(val, "value") else val)
    ...             empty = False
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
    ccc-file
    foo/

Path completions for a run arg:

    >>> cmd_ac(cat.cat, "path", ["bbb"])
    bbb-file
    foo/

Path completions using an operation filter:

    >>> cmd_ac(cat.cat, "path", ["-Fo", "a"])
    aaa-file
    foo/

Path completion with `--sourcecode` option:

    >>> cmd_ac(cat.cat, "path", ["-Fo", "b", "--sourcecode"])
    bbb-file.py
    echo.py
    guild.yml
    inner_source/


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
    0fc1636e7d3653be41f89833776cdb8b

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
    ccc-file
    foo/

Path completion for valid run arg:

    >>> cmd_ac(ls.ls, "path", ["2"])
    bbb-file
    foo/

Path completion for `--sourcecode` option.

    >>> cmd_ac(ls.ls, "path", ["--sourcecode"])
    ccc-file.py
    echo.py
    guild.yml
    inner_source/

Path completion for subfolder

    >>> cmd_ac(ls.ls, "path", [], "foo/")
    foo/ccc-file.py

## Completions for `diff`

    >>> from guild.commands import diff

### `run1` arg

    >>> cmd_ac(diff.diff, "run", [])
    aaa
    bbb
    ccc

### `run2` arg

    >>> cmd_ac(diff.diff, "other_run", [])
    aaa
    bbb
    ccc

### `paths` args

No args - completes paths for latest run:

    >>> cmd_ac(diff.diff, "paths", [])
    ccc-file
    foo/

A run is specified (run 2 is b):

    >>> cmd_ac(diff.diff, "paths", ["2"])
    bbb-file
    foo/

The first run is used for completions when two runs are specified.

    >>> cmd_ac(diff.diff, "paths", ["aaa", "bbb"])
    aaa-file
    foo/

Source code paths:

    >>> cmd_ac(diff.diff, "paths", ["--sourcecode"])
    ccc-file.py
    echo.py
    guild.yml
    inner_source/

    >>> cmd_ac(diff.diff, "paths", ["b", "--sourcecode"])
    bbb-file.py
    echo.py
    guild.yml
    inner_source/

    >>> cmd_ac(diff.diff, "paths", ["--sourcecode", "b"])
    bbb-file.py
    echo.py
    guild.yml
    inner_source/

    >>> cmd_ac(diff.diff, "paths", ["aaa", "bbb", "--sourcecode"])
    aaa-file.py
    echo.py
    guild.yml
    inner_source/

    >>> cmd_ac(diff.diff, "paths", ["aaa", "bbb", "--sourcecode"], "inner_source/")
    inner_source/inner_aaa-file.py

Completions with `--path` can be passed multiple times. validate that completion
works independently at each specification.

    >>> cmd_ac(diff.diff, "paths", ["--path"], "c")
    ccc-file

    >>> cmd_ac(diff.diff, "paths", ["--path", "ccc", "--path"], "foo/")
    foo/ccc-file.py

Path completion with `--working` refers to project path. We shouldn't have the foo folders here.

    >>> cmd_ac(diff.diff, "paths", ["--working"])
    echo.py
    guild.yml

    >>> cmd_ac(diff.diff, "paths", ["--working", "-Fo", "a"])
    echo.py
    guild.yml

    >>> cmd_ac(diff.diff, "paths", ["--working", "aaa", "bbb"])
    echo.py
    guild.yml

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
    ???samples/
    uat/

    >>> cmd_ac(diff.diff, "dir", [], "s")
    samples/


Completed folders that do not have inner folders will not expand further (won't show files)

    >>> cmd_ac(diff.diff, "dir", [], "uat/")
    <empty>

### `cmd` arg

    >>> cmd_ac(diff.diff, "cmd", [])
    ???2to3
    ...
    guild
    guild-env
    ...
    python...
    python3
    ...
    tar...

    >>> cmd_ac(diff.diff, "cmd", [], "guil")
    guild
    guild-env...

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

An op spec can be either an available operation or a Python script.

If we don't specify anything for opspec we get the list of defined
operations.

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

The list includes a directive to remove the colon from COMP_WORDBREAKS
to support proper expansion for operations that contain colons.

If we specify something for opspec, we get matching ops and
scripts. Scripts are represented by the `!!file` directive, which is
used by the bash completion handlers to find matching files.

    >>> run_ac("opspec", [], "echo")
    !!no-colon-wordbreak
    echo
    echo2.py
    echo.py

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

If flag type is not defined and choices aren't available, file path
completion is used.

    >>> run_ac("flags", ["flags"], "nt=")
    batch_fail.py
    echo2.py
    echo.py
    fail.py
    guild.yml
    noisy.py
    noisy_flubber.py
    poly.py
    trial_fail.py
    tune-echo

Flag type is otherwise used to provide possible completions.

Types that don't support completion include int, float and number.

    >>> run_ac("flags", ["flags"], "i=")
    <empty>

    >>> run_ac("flags", ["flags"], "f=")
    <empty>

    >>> run_ac("flags", ["flags"], "n=")
    <empty>

Boolean flags support 'yes' and 'no'.

    >>> run_ac("flags", ["flags"], "b=")
    true
    false

    >>> run_ac("flags", ["flags"], "b=t")
    true

String types including paths support file name completions.

    >>> run_ac("flags", ["flags"], "s=")
    batch_fail.py
    echo...
    poly.py...

    >>> run_ac("flags", ["flags"], "p=")
    batch_fail.py
    echo...
    poly.py...

    >>> run_ac("flags", ["flags"], "ep=")
    batch_fail.py
    echo...
    poly.py...

If a flag starts with '@' it's considered a batch file. In this case
completion is handled by the `!!batchfile` directive.

    >>> run_ac("flags", ["echo"], "@")
    @guild.yml

Flag type

## Completions `operations`

    >>> from guild.commands import operations

### Filter arg

Default:

    >>> cmd_ac(operations.operations, "filters", [])
    echo
    fail
    flags...
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

As do incompletes:

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

    >>> with Env({"_GUILD_COMPLETE": "complete"}):
    ...     [_.value for _ in runs_export.export_runs.params[0].shell_complete(runs_export.export_runs.params[0], "")]
    [...'samples/', 'uat/'...'autcomplete_dummy_archive.zip']

## `help`

TODO: These tests should install a guild package (gpkg) somewhere so that it can be detected.

Help completion supports lookup of installed Guild packages and
directories.

    >>> from guild.commands import help

    >>> with SysPath(prepend=[join_path(dirname(tests_dir()), "external")]):
    ...     with Env({"_GUILD_COMPLETE": "complete"}):
    ...         help._ac_path_or_package(None, None, "")
    [...'samples/'...'uat/']

Filtering completion results should work on both the installed packages and the folders

    >>> with SysPath(prepend=[join_path(dirname(tests_dir()), "external")]):
    ...     with Env({"_GUILD_COMPLETE": "complete"}):
    ...         help._ac_path_or_package(None, None, "sam")
    ['samples/']

    >>> with SysPath(prepend=[join_path(dirname(tests_dir()), "external")]): # doctest: -PY3
    ...     with Env({"_GUILD_COMPLETE": "complete"}):
    ...         help._ac_path_or_package(None, None, "gp")
    ['gpkg.hello']

## `import`

`import` uses the same scheme as `export` (see above).

    >>> from guild.commands import runs_import
    >>> runs_import.import_runs.params[0].name
    'archive'

The archive location for import is a directory.

    >>> with Env({"_GUILD_COMPLETE": "complete"}):
    ...     [_.value for _ in runs_import.import_runs.params[0].shell_complete(runs_import.import_runs.params[0], "")]
    [...'samples/', 'uat/'...'autcomplete_dummy_archive.zip']

## `init`

    >>> from guild.commands import init

Helper to print completions.

    >>> def ac_init(f, incomplete=""):
    ...     from guild.commands import main
    ...     ctx = init.init.make_context("", [])
    ...     ctx.parent = main.main.make_context("", ["-H", project.guild_home])
    ...     with Env({"_GUILD_COMPLETE": "complete"}):
    ...         for val in f(ctx, None, incomplete):
    ...             print(val)

Python versions:

    >>> [_.value for _ in ac_f(init.init, "python")()]
    ['python'...'python3'...]

Target dir - folder list in cwd:

    >>> [_.value for _ in ac_f(init.init, "dir")()]
    [...'samples/', 'uat/']

Guild version or path:

    # TODO: this should check for a guild wheel file somehow
    >>> ac_init(init._ac_guild_version_or_path)
    0.1.0
    ...
    0.7.4
    ...

Guild home - folder list in cwd:

    >>> ac_init(init._ac_guild_home)
    ???samples/
    uat/

Requirements:

    >>> ac_init(init._ac_requirement)
    requirements.txt

Additional Python path - folder list in cwd:

    >>> ac_init(init._ac_path)
    ???samples/
    uat/
