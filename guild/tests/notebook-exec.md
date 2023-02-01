# Running Notebooks

We use the sample 'notebooks' project.

    >>> use_project("notebooks")

Helper functions:

    >>> def nb_source(path):
    ...     data = json.load(open(path))
    ...     for cell in data["cells"]:
    ...         if cell["cell_type"] == "code":
    ...             for line in cell["source"]:
    ...                 print(line.rstrip())

    >>> def nb_output(path):
    ...     data = json.load(open(path))
    ...     for cell in data["cells"]:
    ...         for output in cell["outputs"]:
    ...             if output["output_type"] == "stream":
    ...                 for line in output["text"]:
    ...                     sys.stdout.write(line)

## Replace Assignments

The `flags.ipynb` uses a number of variable assignments.

    >>> nb_source("flags.ipynb")  # doctest: -NORMALIZE_WHITESPACE
    x = 1
    y : int = 2
    z = x + y
    print("z: %s" % z)
    a:float = 1.1; b = 2.2
    c = b - a
    print("c: %f" % c)
    f = True
    s = "hello"
    <BLANKLINE>
    if f:
        print(s)

Guild detects these as flags.

    >>> run("guild run flags.ipynb --help-op")
    Usage: guild run [OPTIONS] flags.ipynb [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      a  (default is 1.1)
      b  (default is 2.2)
      f  (default is yes)
      s  (default is hello)
      x  (default is 1)
      y  (default is 2)
    <exit 0>

When we run this notebook, the defaults are used.

    >>> run("guild run flags.ipynb -y")
    INFO: [guild] Initializing flags.ipynb for run
    INFO: [guild] Executing flags.ipynb...
    z: 3...
    c: 1.100000...
    hello...

    >>> run_dir = run_capture("guild select --dir")

    >>> nb_source(path(run_dir, "flags.ipynb"))  # doctest: -NORMALIZE_WHITESPACE
    x = 1
    y : int = 2
    z = x + y
    print("z: %s" % z)
    a:float = 1.1; b = 2.2
    c = b - a
    print("c: %f" % c)
    f = 1
    s = ...hello...
    <BLANKLINE>
    if f:
        print(s)

    >>> nb_output(path(run_dir, "flags.ipynb"))  # doctest: -NORMALIZE_WHITESPACE
    z: 3
    c: 1.100000
    hello

Guild saves a copy of the generated notebook and generates an HTML report.

    >>> run("guild ls -n")
    add.ipynb
    dep.txt
    deps.ipynb
    flags.html
    flags.ipynb
    guild.yml
    invalid_language.ipynb
    magic.ipynb
    params.ipynb
    reg_301.ipynb

Run with different flag values.

    >>> quiet("""guild run flags.ipynb -y x=1.123 b=3.3 s='Hello hello!
    ...
    ... A second line for hello.
    ...
    ... A third line for hello.'
    ... """)  # doctest: -WINDOWS

Simplified version for Windows (avoid newlines in shell command):

    >>> quiet("guild run flags.ipynb -y x=1.123 b=3.3 s='Hello hello!'")
    ... # doctest: +WINDOWS_ONLY

Output for latest run:

    >>> run_dir = run_capture("guild select --dir")

    >>> nb_source(path(run_dir, "flags.ipynb"))
    ... # doctest: -NORMALIZE_WHITESPACE -NORMALIZE_PATHS -WINDOWS
    x = 1.123
    y : int = 2
    z = x + y
    print("z: %s" % z)
    a:float = 1.1; b = 3.3
    c = b - a
    print("c: %f" % c)
    f = 1
    s = 'Hello hello!\nA second line for hello.\nA third line for hello.'
    <BLANKLINE>
    if f:
        print(s)

    >>> nb_output(path(run_dir, "flags.ipynb"))  # doctest: -WINDOWS
    z: 3.123
    c: 2.200000
    Hello hello!
    A second line for hello.
    A third line for hello.

Corresponding results for Windows:

    >>> nb_source(path(run_dir, "flags.ipynb"))
    ... # doctest: -NORMALIZE_WHITESPACE -NORMALIZE_PATHS +WINDOWS_ONLY
    x = 1.123
    y : int = 2
    z = x + y
    print("z: %s" % z)
    a:float = 1.1; b = 3.3
    c = b - a
    print("c: %f" % c)
    f = 1
    s = 'Hello hello!'
    <BLANKLINE>
    if f:
        print(s)

    >>> nb_output(path(run_dir, "flags.ipynb"))  # doctest: +WINDOWS_ONLY
    z: 3.123
    c: 2.200000
    Hello hello!

## Replace Patterns

The `add.ipynb` notebook requires the use of replacement patterns to
set flag values.

    >>> nb_source("add.ipynb")  # doctest: -NORMALIZE_WHITESPACE
    print(1 + 2)

While we can run the Notebook directly, we cannot affect the behavior.

    >>> run("guild run add.ipynb -y")
    INFO: [guild] Initializing add.ipynb for run
    INFO: [guild] Executing add.ipynb...
    3...

    >>> run_dir = run_capture("guild select --dir")

    >>> nb_source(path(run_dir, "add.ipynb"))  # doctest: -NORMALIZE_WHITESPACE
    print(1 + 2)

    >>> nb_output(path(run_dir, "add.ipynb"))
    3

To modify this notebook for a run, we need to define an operation with
`nb-replace` patterns. The `add` project operation effectively exposes
the values `1` and `2` as flags `x` and `y` respectively.

Run the operation with default values.

    >>> run("guild run add -y")
    INFO: [guild] Initializing add.ipynb for run
    INFO: [guild] Executing add.ipynb...
    30...

The run Notebook reflects the default flag values.

    >>> run_dir = run_capture("guild select --dir")

    >>> nb_source(path(run_dir, "add.ipynb"))  # doctest: -NORMALIZE_WHITESPACE
    print(10 + 20)

    >>> nb_output(path(run_dir, "add.ipynb"))
    30

We can specify different values for `x` and `y`.

    >>> quiet("guild run add x=10 y=-3 -y")

    >>> run_dir = run_capture("guild select --dir")

    >>> nb_source(path(run_dir, "add.ipynb"))  # doctest: -NORMALIZE_WHITESPACE
    print(10 + -3)

    >>> nb_output(path(run_dir, "add.ipynb"))
    7

Flag values are applied in lexical order. As flag values change the
Notebook source as they are applied, subsequent patterns may end up
not matching as expected. Consider the patterns for `x` and `y` in the
`add` operation.

    >>> gf = guildfile.for_dir(".")
    >>> add_op = gf.default_model.get_operation("add")

    >>> add_op.get_flagdef("x").extra["nb-replace"]  # doctest: -NORMALIZE_PATHS
    'print\\((\\d+) \\+ \\d+\\)'

    >>> add_op.get_flagdef("y").extra["nb-replace"]  # doctest: -NORMALIZE_PATHS
    'print\\(\\d+ \\+ (\\d+)\\)'

Note that the patterns match only integer values. Let's run `add` with
float values for `x` and `y`.

    >>> quiet("guild run add x=1.1 y=2.2 -y")

    >>> run_dir = run_capture("guild select --dir")

    >>> nb_source(path(run_dir, "add.ipynb"))  # doctest: -NORMALIZE_WHITESPACE
    print(1.1 + 2)

    >>> nb_output(path(run_dir, "add.ipynb"))
    3.1

The value for `y` is not changed in this case. This is because the
value for `x` is replaced with `1.1`, which causes the pattern for `y`
to not match. `y` is therefore unchanged. To address this, the
developer must provide patterns that tolerate the potential flag value
substitutions where possibly applicable.

## Implied opdef main for notebook

If an operation name ends with `.ipynb` and a main attribute is not
specified, Guild assumes the operation is intended to run as a
notebook.

The operation `deps.ipynb` does not specify either `notebook` or
`main` but is still run as a notebook.

Notebooks generate various warnings that we can safely ignore.

    >>> with Ignore(["Assertion failed: pfd.revents & POLLIN",
    ...              "NoCssSanitizerWarning",
    ...              "warnings.warn"]):
    ...     run("guild run deps.ipynb -y")
    Resolving file:dep.txt
    INFO: [guild] Initializing deps.ipynb for run
    INFO: [guild] Executing deps.ipynb
    Hello!
    <BLANKLINE>
    INFO: [guild] Saving HTML

## Errors

    >>> run("guild run invalid_language.ipynb -y")
    INFO: [guild] Initializing invalid_language.ipynb for run
    INFO: [guild] Executing invalid_language.ipynb...
    Traceback (most recent call last):
    ...
    jupyter_client.kernelspec.NoSuchKernel: No such kernel named xxx
    <exit 1>

## Omitting input in HTML

The `add2` operation provides the option `--html-no-input`, which
omits input cells from the generates HTML.

    ?>> run("guild run add2 -y")
    INFO: [guild] Initializing add.ipynb for run
    INFO: [guild] Executing add.ipynb...
    3...

## Regression tests

### Issue 301

Fix for comments appearning on the last line of a cell.

    >>> run("guild run reg_301.ipynb -y")
    INFO: [guild] Initializing reg_301.ipynb for run
    INFO: [guild] Executing reg_301.ipynb...
