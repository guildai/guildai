# Auto complete

## Init

Context manager to set completions for zsh.

    >>> def ZshCompletion():
    ...     return Env({"_GUILD_COMPLETE": "complete", "_GUILD_AC_SHELL": "zsh"})

    >>> from guild.commands.completion_impl import _current_shell
    >>> with ZshCompletion():
    ...     _current_shell()
    'zsh'

Helper functions:

    >>> def ac_f(cmd, param_name):
    ...     for param in cmd.params:
    ...         if param.name == param_name:
    ...             assert param.shell_complete, (param, cmd)
    ...             def f(**kw):
    ...                 with ZshCompletion():
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

Create a directory with files to isolated tests.

    >>> test_tmp = mkdtemp()
    >>> touch(path(test_tmp, "foo.md"))
    >>> touch(path(test_tmp, "bar.md"))
    >>> touch(path(test_tmp, "foo.txt"))
    >>> touch(path(test_tmp, "run-docs.md"))

A helper to show completions.

    >>> def ac_check_tests(incomplete, subdir=""):
    ...     ctx = check.check.make_context("", [])
    ...     with ZshCompletion():
    ...         with Chdir(test_tmp):
    ...            for val in check._ac_all_tests(ctx, None, incomplete):
    ...                print(val)

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
    bar.md
    foo.md
    foo.txt
    run-docs.md

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
    run-docs.md

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

    >>> runs = project.list_runs()

    >>> runs[0].id, project.ls(runs[0])
    ('ccc', ['bar.txt', 'c.out', 'foo.txt', 'foo/xxx.txt', 'foo/yyy.txt'])

    >>> runs[1].id, project.ls(runs[1])
    ('bbb', ['b.out', 'bar.txt', 'foo.txt', 'foo/xxx.txt', 'foo/yyy.txt'])

    >>> runs[2].id, project.ls(runs[2])
    ('aaa', ['a.out', 'bar.txt', 'foo.txt', 'foo/xxx.txt', 'foo/yyy.txt'])

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
    ...     with ZshCompletion():
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
    bar.txt
    c.out
    foo.txt
    foo/

    >>> cmd_ac(cat.cat, "path", [], "c")
    c.out

Path completions for a run arg:

    >>> cmd_ac(cat.cat, "path", ["bbb"])
    b.out
    bar.txt
    foo.txt
    foo/

    >>> cmd_ac(cat.cat, "path", ["bbb"], "f")
    foo.txt
    foo/

    >>> cmd_ac(cat.cat, "path", ["bbb"], "foo/")
    foo/xxx.txt
    foo/yyy.txt

    >>> cmd_ac(cat.cat, "path", ["bbb"], "b")
    b.out
    bar.txt

Path completions using an operation filter:

    >>> cmd_ac(cat.cat, "path", ["-Fo", "a"])
    a.out
    bar.txt
    foo.txt
    foo/

    >>> cmd_ac(cat.cat, "path", ["-Fo", "a"], "foo")
    foo.txt
    foo/

    >>> cmd_ac(cat.cat, "path", ["-Fo", "a"], "foo/")
    foo/xxx.txt
    foo/yyy.txt

Path completion with `--sourcecode` option:

    >>> cmd_ac(cat.cat, "path", ["-Fo", "b", "--sourcecode"])
    b.src.out
    echo.py
    guild.yml

    >>> cmd_ac(cat.cat, "path", ["-Fo", "b", "--sourcecode"], "ec")
    echo.py

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

    >>> cmd_ac(cat.cat, "filter_digest", [], "a")
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
    bar.txt
    c.out
    foo.txt
    foo/

    >>> cmd_ac(ls.ls, "path", [], "b")
    bar.txt

Path completion for valid run arg:

    >>> cmd_ac(ls.ls, "path", ["2"])
    b.out
    bar.txt
    foo.txt
    foo/

    >>> cmd_ac(ls.ls, "path", ["2"], "b")
    b.out
    bar.txt

Path completion for `--sourcecode` option.

    >>> cmd_ac(ls.ls, "path", ["--sourcecode"])
    c.src.out
    echo.py
    guild.yml

    >>> cmd_ac(ls.ls, "path", ["bbb", "--sourcecode"])
    b.src.out
    echo.py
    guild.yml

    >>> cmd_ac(ls.ls, "path", ["bbb", "--sourcecode"], "g")
    guild.yml

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
    bar.txt
    c.out
    foo.txt
    foo/

    >>> cmd_ac(diff.diff, "paths", [], "z")
    <empty>

    >>> cmd_ac(diff.diff, "paths", [], "f")
    foo.txt
    foo/

A run is specified:

    >>> cmd_ac(diff.diff, "paths", ["2"])
    b.out
    bar.txt
    foo.txt
    foo/

The first run is used for completions when two runs are specified.

    >>> cmd_ac(diff.diff, "paths", ["aaa", "bbb"])
    a.out
    bar.txt
    foo.txt
    foo/

    >>> cmd_ac(diff.diff, "paths", ["bbb", "aaa"])
    b.out
    bar.txt
    foo.txt
    foo/

Source code paths:

    >>> cmd_ac(diff.diff, "paths", ["--sourcecode"])
    c.src.out
    echo.py
    guild.yml

    >>> cmd_ac(diff.diff, "paths", ["b", "--sourcecode"])
    b.src.out
    echo.py
    guild.yml

    >>> cmd_ac(diff.diff, "paths", ["--sourcecode", "a"])
    a.src.out
    echo.py
    guild.yml

    >>> cmd_ac(diff.diff, "paths", ["aaa", "bbb", "--sourcecode"])
    a.src.out
    echo.py
    guild.yml

    >>> cmd_ac(diff.diff, "paths", ["bbb", "aaa", "--sourcecode"])
    b.src.out
    echo.py
    guild.yml

Path completion with `--working` refers to project path:

    >>> cmd_ac(diff.diff, "paths", ["--working"])
    echo.py
    guild.yml

    >>> cmd_ac(diff.diff, "paths", ["--working", "-Fo", "a"])
    echo.py
    guild.yml

    >>> cmd_ac(diff.diff, "paths", ["--working", "aaa", "bbb"])
    echo.py
    guild.yml

Completions with `--dir` refer to the specified run path:

    >>> tmp = mkdtemp()
    >>> touch(path(tmp, "aaa.txt"))
    >>> touch(path(tmp, "bbb.txt"))
    >>> mkdir(path(tmp, "subdir"))

    >>> cmd_ac(diff.diff, "paths", ["--dir", tmp])
    aaa.txt
    bbb.txt
    subdir/

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

TODO reinstate:

    >> cmd_ac(diff.diff, "dir", [])
    !!dir

/TODO

### `cmd` arg

TODO reinstate with a controlled cmd test:

    >> cmd_ac(diff.diff, "cmd", [])
    !!command

/TODO

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
    batch_fail.py
    echo2.py
    echo.py
    fail.py
    noisy.py
    noisy_flubber.py
    poly.py
    trial_fail.py

The list includes a directive to remove the colon from COMP_WORDBREAKS
to support proper expansion for operations that contain colons.

If we specify something for opspec, we get matching ops and scripts.

    >>> run_ac("opspec", [], "ech")
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
identified. zsh wants the format 'name=val' (bash just lists the
choice values - see [autocomplete-bash.md](autocomplete-bash.md)).

    >>> run_ac("flags", ["echo"], "z=")
    z=a
    z=b
    z=c
    z=d

    >>> run_ac("flags", ["flags"], "c=")
    c=123
    c=1.123
    c=hello
    c=false

Choices are limited as well.

    >>> run_ac("flags", ["echo"], "z=d")
    z=d

    >>> run_ac("flags", ["flags"], "c=hel")
    c=hello

If flag type is not defined and choices aren't available, file path
completion is used.

    >>> run_ac("flags", ["flags"], "nt=")
    nt=batch_fail.py
    nt=echo2.py
    nt=echo.py
    nt=fail.py
    nt=guild.yml
    nt=noisy.py
    nt=noisy_flubber.py
    nt=poly.py
    nt=trial_fail.py
    nt=tune-echo

Flag type is otherwise used to provide possible completions.

Types that don't support completion: int, float and number.

    >>> run_ac("flags", ["flags"], "i=")
    i=
    !!nospace

    >>> run_ac("flags", ["flags"], "f=")
    f=
    !!nospace

    >>> run_ac("flags", ["flags"], "n=")
    n=
    !!nospace

Boolean flags support 'true' and 'false'.

    >>> run_ac("flags", ["flags"], "b=")
    b=true
    b=false

    >>> run_ac("flags", ["flags"], "b=t")
    b=true

String types (including paths) support file name completions.

    >>> run_ac("flags", ["flags"], "s=")
    s=batch_fail.py
    s=echo2.py
    s=echo.py
    s=fail.py
    s=guild.yml
    s=noisy.py
    s=noisy_flubber.py
    s=poly.py
    s=trial_fail.py
    s=tune-echo

    >>> run_ac("flags", ["flags"], "s=e")
    s=echo2.py
    s=echo.py

    >>> run_ac("flags", ["flags"], "p=")
    p=batch_fail.py
    p=echo2.py
    p=echo.py
    p=fail.py
    p=guild.yml
    p=noisy.py
    p=noisy_flubber.py
    p=poly.py
    p=trial_fail.py
    p=tune-echo

    >>> run_ac("flags", ["flags"], "p=tune-")
    p=tune-echo

    >>> run_ac("flags", ["flags"], "ep=")
    ep=batch_fail.py
    ep=echo2.py
    ep=echo.py
    ep=fail.py
    ep=guild.yml
    ep=noisy.py
    ep=noisy_flubber.py
    ep=poly.py
    ep=trial_fail.py
    ep=tune-echo

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

    >>> export_tmp = mkdtemp()
    >>> touch(path(export_tmp, "xxx.zip"))
    >>> mkdir(path(export_tmp, "yyy"))

    >>> with ZshCompletion():
    ...     with Chdir(export_tmp):
    ...         [_.value for _ in runs_export.export_runs.params[0].shell_complete(None, "")]
    ['yyy/', 'xxx.zip']

## `help`

Help completion supports lookup of installed Guild packages and
directories.

    >>> from guild.commands import help

    >>> help_tmp = mkdtemp()
    >>> mkdir(path(help_tmp, "yyy"))
    >>> mkdir(path(help_tmp, "zzz"))

    >>> with ZshCompletion():
    ...     with Chdir(help_tmp):
    ...        help._ac_path_or_package(None, None, "")
    [...'yyy/', 'zzz/']

## `import`

`import` uses the same scheme as `export` (see above).

    >>> from guild.commands import runs_import
    >>> runs_import.import_runs.params[0].name
    'archive'

The archive location for import is a directory or a zip file.

    >>> with ZshCompletion():
    ...     with Chdir(export_tmp):
    ...         [_.value for _ in runs_import.import_runs.params[0].shell_complete(None, "")]
    ['yyy/', 'xxx.zip']

## `init`

    >>> from guild.commands import init

    >>> init_tmp = mkdtemp()
    >>> mkdir(path(init_tmp, "dir-1"))
    >>> mkdir(path(init_tmp, "dir-2"))
    >>> touch(path(init_tmp, "aaa.whl"))
    >>> touch(path(init_tmp, "bbb.whl"))
    >>> touch(path(init_tmp, "xxx.txt"))
    >>> touch(path(init_tmp, "yyy.txt"))

Helper to print completions for init command.

    >>> def ac_init(f, incomplete=""):
    ...     from guild.commands import main
    ...     ctx = init.init.make_context("", [])
    ...     ctx.parent = main.main.make_context("", ["-H", project.guild_home])
    ...     with ZshCompletion():
    ...         with Chdir(init_tmp):
    ...            for val in f(ctx, None, incomplete):
    ...                print(val.value if hasattr(val, "value") else val)

Python versions:

    >>> ac_f(init.init, "python")()
    ['python...']

Target dir:

    >>> with Chdir(init_tmp):
    ...     ac_f(init.init, "dir")()
    ['dir-1/', 'dir-2/']

Guild version or path:

    >>> ac_init(init._ac_guild_version_or_path)
    ???aaa.whl
    bbb.whl

Guild home:

    ac_init(init._ac_guild_home)

Requirements:

    >>> ac_init(init._ac_requirement)
    xxx.txt
    yyy.txt

Additional Python path:

    >>> ac_init(init._ac_dir)
    dir-1/
    dir-2/
