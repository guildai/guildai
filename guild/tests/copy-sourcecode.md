# Copying source code

These tests exercise each of the operations defined in the
`copy-sourcecode` sample project.

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
    ...     with Env({"NO_WARN_RUNDIR": "1"}):
    ...         project.run(op, run_dir=run_dir)
    ...     find(join_path(run_dir, ".guild/sourcecode"))

## Default files

Guild copies text files by default.

    >>> print_config("default")
    <none>

    >>> run("default")
    .gitattributes
    __pycache__/...
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

    >>> run("alt-root")
    b.txt

## Include additional files

To include additional files that are not otherwise selected (i.e. are
not text files), use explicit includes.

    >>> print_config("include-png")
    op-sourcecode:
    - include: '*.png'

    >>> run("include-png")
    <BLANKLINE>
    .gitattributes
    __pycache__/...
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

    >>> run("exclude-py")
    .gitattributes
    __pycache__/...
    a.txt
    empty
    guild.yml
    subdir/b.txt

## Disabling source code copies

There are multiple ways to disable source code copies altogether.

Using no (False):

    >>> print_config("disabled")
    op-sourcecode: false

    >>> run("disabled")
    <empty>

Specifying an emty list of specs:

    >>> print_config("disabled2")
    op-sourcecode: []

    >>> run("disabled2")
    <empty>

Using an exclude spec:

    >>> print_config("disabled3")
    op-sourcecode:
    - exclude: '*'

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

    >>> run("m1:op")
    .gitattributes
    __pycache__/...
    empty
    guild.yml
    subdir/b.txt
    subdir/logo.png

Model disables source code copy:

    >>> print_config("m2:op1")
    model-sourcecode: false

    >>> run("m2:op1")
    <empty>

Model disables source code copy but operation re-enables it to copy
only py and yml files.

    >>> print_config("m2:op2")
    model-sourcecode: false
    op-sourcecode:
    - '*.py'
    - '*.yml'

    >>> run("m2:op2")
    guild.yml
    hello.py

Model enables all files to copy:

    >>> print_config("m3:op1")
    model-sourcecode: '*'

    >>> run("m3:op1")
    <BLANKLINE>
    .gitattributes
    __pycache__/...
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

    >>> run("m3:op2")
    <empty>
