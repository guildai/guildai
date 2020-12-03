# Notebooks Support

## Import Notebook Flags

Notebook support is implemented by the `ipynb` plugin.

    >> from guild.plugins import ipynb

### Global Assigns

Top-level assigns are treated as flags, just as they are in Python
modules.

    >> flags_ipynb = sample("projects", "notebooks", "flags.ipynb")

    >> with LogCapture() as logs:
    ...     flags_data = ipynb._flags_data_for_notebook(flags_ipynb)
    >> pprint(flags_data)
    {'a': {'default': 1.1, 'type': 'number'},
     'b': {'default': 2.2, 'type': 'number'},
     'f': {'default': True, 'type': 'boolean'},
     's': {'default': 'hello', 'type': 'string'},
     'x': {'default': 1, 'type': 'number'},
     'y': {'default': 2, 'type': 'number'}}

Verify that we didn't get any warnings while processing the notebook
source.

    >> logs.print_all()

The `flags` operation in the associated Guild file runs `flags.ipynb`
as a notebook. The operation is configured to import all flags but
`b`, which is skipped.

    >> gf = guildfile.for_dir(sample("projects", "notebooks"))

    >> from guild import help
    >> print(help.guildfile_console_help(gf, strip_ansi_format=True))
    ???
    BASE OPERATIONS
    ...
    <BLANKLINE>
        flags
          Flags:
            a  (default is 1.1)
            f  (default is yes)
            s  (default is hello)
            x  (default is 11)
            y  (default is 22)
    <BLANKLINE>
    ...

## nbexec

The `nbexec` module handles Notebook execution.

    >>> from guild.plugins import nbexec

### Apply Flag Values to Source

The function `_replace_assigns_for_source_lines` implements support
for replacing Notebook cell source with flag values.

The function requires cell source lines and a "apply flags" state
object.

Here's a helper function to use the function to convert a block of
code and flags to code containing flag assignments.

    >>> class _ApplyFlagsStateProxy(object):
    ...     def __init__(self, flags):
    ...         self.flags = flags

    >>> def apply_flags(src, **flags):
    ...     state = _ApplyFlagsStateProxy(flags)
    ...     lines_in = [line + "\n" for line in src.strip().split("\n")]
    ...     lines_out = nbexec._replace_assigns_for_source_lines(lines_in, state)
    ...     print("".join(lines_out))

Simple example:

    >>> apply_flags("x = 1", x=11)
    x = 11

Nothing is changed where there are no flags.

    >>> apply_flags("""
    ... # Sample code
    ... i = 1
    ... f = 1.123
    ... s = "hello"  # comment
    ... b = True # another comment
    ...
    ... print(i, f, s, b)
    ... """)
    # Sample code
    i = 1
    f = 1.123
    s = "hello"  # comment
    b = True # another comment
    <BLANKLINE>
    print(i, f, s, b)

Providing some flag values:

    >>> apply_flags("""
    ... # Sample code
    ... i = 1
    ... f = 1.123
    ... s = "hello"
    ... b = True
    ...
    ... print(i, f, s, b)
    ... """, i=22, f=45.678, s="hola", b=0)
    # Sample code
    i = 22
    f = 45.678
    s = 'hola'
    b = 0
    <BLANKLINE>
    print(i, f, s, b)

White space and comments are preserved.

    >>> apply_flags("x  =1  # a comment", x="foo bar")
    x  ='foo bar'  # a comment

None values are used when provided.

    >>> apply_flags("x = 1", x=None)
    x = None

When multiple targets are specified, only the last target is used as a
flag.

    >>> apply_flags("x = y = 1", x=123, y="hello there")
    x = y = 'hello there'
    <BLANKLINE>

    >>> apply_flags("x = y = 1", x=123)
    x = y = 1
    <BLANKLINE>

Flags replace assignments that span multiple lines.

    >>> apply_flags("""
    ... a = 1
    ... b = '''Line 1
    ... Line 2
    ... Line 3
    ... '''
    ... """, b=666
    ... )
    a = 1
    b = 666

    >>> apply_flags("""x = (
    ...
    ...        1
    ...     )
    ... """, x=12345)
    x = (
    <BLANKLINE>
           12345
        )

    >>> apply_flags("""x = \
    ... \
    ... 1
    ... """, x=True)
    x = True

    >>> apply_flags("""x = y = '''Line 1
    ... Line 2
    ...
    ... Line 3
    ... ''' # a conmment
    ... for i in range(x):
    ...     print(i)
    ... z = '''
    ... 1.1234
    ... '''
    ... # Another comment
    ... """, y="Another value", z=2.2345)
    x = y = 'Another value' # a conmment
    for i in range(x):
        print(i)
    z = 2.2345
    # Another comment

If source contains a syntax error, it is returned unmodified. Guild
logs a warning.

    >>> with LogCapture() as logs:
    ...     apply_flags("'unterminated string")
    'unterminated string

    >> logs.print_all()
    WARNING: error parsing Python source "'unterminated string": EOL
    while scanning string literal (<unknown>, line 1)

### nb-replace

Flag values can be updated in Notebook cells using `nb-repl` flag
attributes.

`nb-repl` is a pattern that uses capture groups to indicate where flag
values should be inserted.

The `_replace_flag_ref` implements the replacement logic.

    >> _replace_flag_ref = nbexec._replace_flag_ref

Here's a case where a variable assignment is updated with a new value.

    >> _replace_flag_ref("foo = (36)", 12, "foo = 36")
    'foo = 12'

If the pattern doesn't match, the cell is left unchanged.

    >> _replace_flag_ref("foo = (36)", 12, "foo = 42")
    'foo = 42'

Regular expressions can be used inside and outside the capture groups
as needed.

    >> _replace_flag_ref("foo = (.*) # update me", 12, "foo = 42 # update me")
    'foo = 12 # update me'

A non-capturing group can be used to match but not replace.

    >> _replace_flag_ref("(?:foo|bar) = (.*) # update me", 12, "foo = 42 # update me")
    'foo = 12 # update me'

Multiple groups can be used to include the flag value multiple times.

    >> print(_replace_flag_ref("a1=(\".*\"), a2=(\".*\")", "hi", """
    ... def f(a1="a1", a2="a2"):
    ...     print(a1, a2)
    ... """))
    def f(a1='hi', a2='hi'):
        print(a1, a2)

If a pattern doesn't define a capture group, the entire string is
replaced when matched.

    >> _replace_flag_ref("1234", 4567, "The value is 1234")
    'The value is 4567'

## Running Notebooks

We use the sample 'notebooks' project.

    >> project = Project(sample("projects", "notebooks"))

The 'add' operation adds two numbers, `x` and `y`, which can be set as
flags.

    >> project.run("add", flags={"x": 100, "y": 200})
    [NbConvertApp] Converting notebook .../add.ipynb to notebook...
    [NbConvertApp] Converting notebook .../add.ipynb to html...

    >> import json
    >> generated_ipynb = json.load(open(path(project.list_runs()[0].dir, "add.ipynb")))
    >> generated_ipynb["nbformat"]
    4

    >> pprint(generated_ipynb["cells"])
    [{'cell_type': 'code',
      'execution_count': 1,
      'metadata': ...
      'outputs': [{'name': 'stdout',
                   'output_type': 'stream',
                   'text': ['300\n']}],
      'source': ['print(100 + 200)']}]

You can run the Notebook directly. In this case, there are no flags
because we don't know anything about the notebook.

    >> project.run("add.ipynb")
    [NbConvertApp] Converting notebook .../add.ipynb to notebook...
    [NbConvertApp] Converting notebook .../add.ipynb to html...

    >> project.print_runs(flags=True, labels=True)
    add.ipynb
    add        x=100 y=200  x=100 y=200

The generated Notebook is the same as the original.

    >> generated_ipynb = json.load(open(path(project.list_runs()[0].dir, "add.ipynb")))
    >> generated_ipynb["nbformat"]
    4

    >> pprint(generated_ipynb["cells"])
    [{'cell_type': 'code',
      'execution_count': 1,
      'metadata': ...
      'outputs': [{'name': 'stdout',
                   'output_type': 'stream',
                   'text': ['3\n']}],
      'source': ['print(1 + 2)']}]

## Errors

    >> project.run("invalid_language.ipynb")
    [NbConvertApp] Converting notebook .../invalid_language.ipynb to notebook
    Traceback (most recent call last):
    ...
    jupyter_client.kernelspec.NoSuchKernel: No such kernel named xxx
    <exit 1>
