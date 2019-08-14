# Copying source code

These tests exercise each of the operations defined in the
[`copy-sourcecode`](samples/projects/copy-sourcecode/guild.yml) sample
project.

    >>> project_dir = sample("projects/copy-sourcecode")
    >>> project = Project(project_dir)

Here's a helper function for printing operation sourcecode config.

    >>> import yaml
    >>> data = yaml.safe_load(open(join_path(project_dir, "guild.yml"), "r"))

    >>> from guild import util
    >>> def print_config(op):
    ...     parts = op.split(":")
    ...     if len(parts) == 1:
    ...         model = ""
    ...     else:
    ...         model, op = parts
    ...     for model_data in data:
    ...         if model_data["model"] == model:
    ...             break
    ...     else:
    ...         assert False, (model, op)
    ...     config = {}
    ...     if "sourcecode" in model_data:
    ...         config["model-sourcecode"] = model_data["sourcecode"]
    ...     op_data = model_data["operations"][op]
    ...     if "sourcecode" in op_data:
    ...         config["op-sourcecode"] = op_data["sourcecode"]
    ...     if config:
    ...         print(util.encode_yaml(config).strip())
    ...     else:
    ...         print("<none>")

Here's a helper function that runs the specified operation and prints
the list of copied source code files for the generated run.

    >>> def run(op):
    ...     run_dir = mkdtemp()
    ...     project.run_quiet(op, run_dir=run_dir)
    ...     find(join_path(run_dir, ".guild/sourcecode"))

And a helper for previewing source code copies:

    >>> def preview(op):
    ...     project.run(op, test_sourcecode=True)

## Default files

Guild copies text files by default.

    >>> print_config("default")
    <none>

Here's a preview of the copy, which shows the rules that are applied:

    >>> preview("default")
    Copying from the current directory
    Rules:
      exclude dir '.*'
      exclude dir '*' (with '.guild-nocopy')
      exclude dir '*' (with 'bin/activate')
      include text '*' (size < 1048577, max match 100)
    Selected for copy:
      ./.gitattributes
      ./a.txt
      ./empty
      ./guild.yml
      ./hello.py
      ./subdir/b.txt
    Skipped:
      ./hello.pyc
      ./subdir/logo.png

And the copied files:

    >>> run("default")
    .gitattributes
    a.txt
    empty
    guild.yml
    hello.py
    subdir/b.txt

## Alternate root

Specify `root` to change the directory that files are copied from.

    >>> print_config("alt-root")
    op-sourcecode:
      root: subdir

    >>> preview("alt-root")
    Copying from 'subdir'
    Rules:
      exclude dir '.*'
      exclude dir '*' (with '.guild-nocopy')
      exclude dir '*' (with 'bin/activate')
      include text '*' (size < 1048577, max match 100)
    Selected for copy:
      subdir/b.txt
    Skipped:
      subdir/logo.png

    >>> run("alt-root")
    b.txt

## Include additional files

To include additional files that are not otherwise selected (i.e. are
not text files), use explicit includes.

    >>> print_config("include-png")
    op-sourcecode:
    - include: '*.png'

This rule is applied after the default rules:

    >>> preview("include-png")
    Copying from the current directory
    Rules:
      exclude dir '.*'
      exclude dir '*' (with '.guild-nocopy')
      exclude dir '*' (with 'bin/activate')
      include text '*' (size < 1048577, max match 100)
      include '*.png'
    Selected for copy:
      ./.gitattributes
      ./a.txt
      ./empty
      ./guild.yml
      ./hello.py
      ./subdir/b.txt
      ./subdir/logo.png
    Skipped:
      ./hello.pyc

The `png` file is copied along with the default files:

    >>> run("include-png")
    <BLANKLINE>
    .gitattributes
    a.txt
    empty
    guild.yml
    hello.py
    subdir/b.txt
    subdir/logo.png

## Override defaults

Defaults can be overridden with explicit string patterns.

Only png files:

    >>> print_config("only-png")
    op-sourcecode: '*.png'

When only string patterns are specified for an include, Guild
implicitly inserts an exclude '*' before adding the patterns. This
ensures that only those files matching the specified patterns are selected.

    >>> preview("only-png")
    Copying from the current directory
    Rules:
      exclude dir '.*'
      exclude dir '*' (with '.guild-nocopy')
      exclude dir '*' (with 'bin/activate')
      include text '*' (size < 1048577, max match 100)
      exclude '*'
      include '*.png'
    Selected for copy:
      ./subdir/logo.png
    Skipped:
      ./.gitattributes
      ./a.txt
      ./empty
      ./guild.yml
      ./hello.py
      ./hello.pyc
      ./subdir/b.txt

    >>> run("only-png")
    subdir/logo.png

Only py files:

    >>> print_config("only-py")
    op-sourcecode:
    - '*.py'

    >>> run("only-py")
    hello.py

Only png and py files:

    >>> print_config("png-and-py")
    op-sourcecode:
    - '*.png'
    - '*.py'

    >>> run("png-and-py")
    hello.py
    subdir/logo.png

This logic can be alternatively specified by first excluding all
matches and then including those to select.

    >>> print_config("only-py2")
    op-sourcecode:
    - exclude: '*'
    - include: '*.py'

    >>> run("only-py2")
    hello.py

## Excluding some default files

Some of the default files can be excluded by specifying one or more
exclude specs.

    >>> print_config("exclude-py")
    op-sourcecode:
    - exclude: '*.py'

    >>> preview("exclude-py")
    Copying from the current directory
    Rules:
      exclude dir '.*'
      exclude dir '*' (with '.guild-nocopy')
      exclude dir '*' (with 'bin/activate')
      include text '*' (size < 1048577, max match 100)
      exclude '*.py'
    Selected for copy:
      ./.gitattributes
      ./a.txt
      ./empty
      ./guild.yml
      ./subdir/b.txt
    Skipped:
      ./hello.py
      ./hello.pyc
      ./subdir/logo.png

    >>> run("exclude-py")
    .gitattributes
    a.txt
    empty
    guild.yml
    subdir/b.txt

## Disabling source code copies

There are multiple ways to disable source code copies altogether.

Using no (False):

    >>> print_config("disabled")
    op-sourcecode: false

    >>> preview("disabled")
    Copying from the current directory
    Rules:
      exclude '*'
    Source code copy disabled

    >>> run("disabled")
    <empty>

Specifying an emty list of specs:

    >>> print_config("disabled2")
    op-sourcecode: []

    >>> preview("disabled2")
    Copying from the current directory
    Rules:
      exclude '*'
    Source code copy disabled

    >>> run("disabled2")
    <empty>

Using an exclude spec:

    >>> print_config("disabled3")
    op-sourcecode:
    - exclude: '*'

    >>> preview("disabled3")
    Copying from the current directory
    Rules:
      exclude dir '.*'
      exclude dir '*' (with '.guild-nocopy')
      exclude dir '*' (with 'bin/activate')
      include text '*' (size < 1048577, max match 100)
      exclude '*'
    Source code copy disabled

    >>> run("disabled3")
    <empty>

## Model and op config interactions

Source code config can be specified at the model level as well as the
operaiton level. Model level specs are applied first, followed by op
level specs. This lets operations append rules to the model level
rules, which are evaluated subsequently and therefore can change model
level select behavior.

Model adds png and operation excludes `*.py` and `a.*` files:

    >>> print_config("m1:op")
    model-sourcecode:
    - include: subdir/logo.png
    op-sourcecode:
    - exclude:
      - '*.py'
      - a.*

    >>> preview("m1:op")
    Copying from the current directory
    Rules:
      exclude dir '.*'
      exclude dir '*' (with '.guild-nocopy')
      exclude dir '*' (with 'bin/activate')
      include text '*' (size < 1048577, max match 100)
      include 'subdir/logo.png'
      exclude '*.py', 'a.*'
    Selected for copy:
      ./.gitattributes
      ./empty
      ./guild.yml
      ./subdir/b.txt
      ./subdir/logo.png
    Skipped:
      ./a.txt
      ./hello.py
      ./hello.pyc

    >>> run("m1:op")
    .gitattributes
    empty
    guild.yml
    subdir/b.txt
    subdir/logo.png

Model disables source code copy:

    >>> print_config("m2:op1")
    model-sourcecode: false

    >>> preview("m2:op1")
    Copying from the current directory
    Rules:
      exclude '*'
    Source code copy disabled

    >>> run("m2:op1")
    <empty>

Model disables source code copy but operation re-enables it to copy
only py and yml files.

    >>> print_config("m2:op2")
    model-sourcecode: false
    op-sourcecode:
    - '*.py'
    - '*.yml'

    >>> preview("m2:op2")
    Copying from the current directory
    Rules:
      exclude dir '.*'
      exclude dir '*' (with '.guild-nocopy')
      exclude dir '*' (with 'bin/activate')
      include text '*' (size < 1048577, max match 100)
      exclude '*'
      include '*.py'
      include '*.yml'
    Selected for copy:
      ./guild.yml
      ./hello.py
    Skipped:
      ./.gitattributes
      ./a.txt
      ./empty
      ./hello.pyc
      ./subdir/b.txt
      ./subdir/logo.png

    >>> run("m2:op2")
    guild.yml
    hello.py

Model enables all files to copy:

    >>> print_config("m3:op1")
    model-sourcecode: '*'

    >>> preview("m3:op1")
    Copying from the current directory
    Rules:
      exclude dir '.*'
      exclude dir '*' (with '.guild-nocopy')
      exclude dir '*' (with 'bin/activate')
      include text '*' (size < 1048577, max match 100)
      exclude '*'
      include '*'
    Selected for copy:
      ./.gitattributes
      ./a.txt
      ./empty
      ./guild.yml
      ./hello.py
      ./hello.pyc
      ./subdir/b.txt
      ./subdir/logo.png
    Skipped:

    >>> run("m3:op1")
    <BLANKLINE>
    .gitattributes
    a.txt
    empty
    guild.yml
    hello.py
    hello.pyc
    subdir/b.txt
    subdir/logo.png

Model enables all files to copy, operation disables source code copy:

    >>> print_config("m3:op2")
    model-sourcecode: '*'
    op-sourcecode: false

    >>> preview("m3:op2")
    Copying from the current directory
    Rules:
      exclude '*'
    Source code copy disabled

    >>> run("m3:op2")
    <empty>

## Source code for Python scripts

When running a Python script, Guild generates a model proxy that is
used to run the script. The proxy uses a special `sourcecode` spec
that limits the source code copied to text files in the current
directory.

For our sample project, there is no sourcecode configuration for
`hello.py`:

    >>> print_config("hello.py")
    Traceback (most recent call last):
    KeyError: 'hello.py'

The script model proxy adds an exclude '*' of type 'dir' to ensure
that directories are not included in the copy.

    >>> preview("hello.py")
    Copying from the current directory
    Rules:
      exclude dir '.*'
      exclude dir '*' (with '.guild-nocopy')
      exclude dir '*' (with 'bin/activate')
      include text '*' (size < 1048577, max match 100)
      exclude dir '*'
    Selected for copy:
      ./.gitattributes
      ./a.txt
      ./empty
      ./guild.yml
      ./hello.py
    Skipped:
      ./hello.pyc

Here are the copied files:

    >>> run("hello.py")
    .gitattributes
    a.txt
    empty
    guild.yml
    hello.py
