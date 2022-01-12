# Notebook Support

## Import Notebook Flags

Notebook support is implemented by the `ipynb` plugin.

    >>> from guild.plugins import ipynb

### Global Assigns

Top-level assigns are treated as flags, just as they are in Python
modules.

    >>> flags_ipynb = sample("projects", "notebooks", "flags.ipynb")

    >>> with LogCapture() as logs:
    ...     flags_data = ipynb._flags_data_for_notebook(flags_ipynb)
    >>> pprint(flags_data)
    {'a': {'default': 1.1, 'type': 'float'},
     'b': {'default': 2.2, 'type': 'number'},
     'f': {'default': True, 'type': 'boolean'},
     's': {'default': 'hello', 'type': 'string'},
     'x': {'default': 1, 'type': 'number'},
     'y': {'default': 2, 'type': 'int'}}

Verify that we didn't get any warnings while processing the notebook
source.

    >>> logs.print_all()

The `flags` operation in the associated Guild file runs `flags.ipynb`
as a notebook. The operation is configured to import all flags but
`b`, which is skipped.

    >>> gf = guildfile.for_dir(sample("projects", "notebooks"))

    >>> from guild import help
    >>> print(help.guildfile_console_help(gf, strip_ansi_format=True))
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

## Apply Flag Values to Source

Guild supports two methods of value assigment:

- Replace single value assignments with a new flag value
- Replace matching regular expressions with flag values

### Replace Value Assignments

The function `guild.plugins.nbexec._replace_flag_assign_vals`
implements support for replacing Notebook cell source with flag
values.

    >>> from guild.plugins.nbexec import _replace_flag_assign_vals

The function requires cell source lines and a "apply flags" state
object.

Here's a helper function to use the function to convert a block of
code and flags to code containing flag assignments.

    >>> class _ApplyFlagsStateProxy(object):
    ...     def __init__(self, flags, flags_extra):
    ...         self.flags = flags
    ...         self.flags_extra = flags_extra

    >>> def apply_flags(src, **flags):
    ...     state = _ApplyFlagsStateProxy(flags, {})
    ...     out = _replace_flag_assign_vals(src, state)
    ...     print(out)

Examples:

    >>> apply_flags("x = 1", x=11)
    x = 11

    >>> apply_flags("x = -1", x=11)
    x = 11

    >>> apply_flags("x = +1", x=11)
    x = 11

    >>> apply_flags("x = 1", x=-11)
    x = -11

    >>> apply_flags("x = -1", x=-11)
    x = -11

    >>> apply_flags("x = +1", x=-11)
    x = -11

    >>> apply_flags("x = 1.123", x=2.234)
    x = 2.234

    >>> apply_flags("x = -11111111111111111111111111; y = -2", x=-33333333333, y=-444)
    x = -33333333333; y = -444

    >>> apply_flags("x = 1; y = 2", x=666, y=777)
    x = 666; y = 777

    >>> apply_flags("x = -1\n", x='hello', y=777)
    x = 'hello'
    <BLANKLINE>

    >>> apply_flags("x = 1; y = 2; z=-3", x=666, y=777, z=888)
    x = 666; y = 777; z=888

    >>> apply_flags("x = -1\ny = 2", x=666, y=777)
    x = 666
    y = 777

    >>> apply_flags("x = 1  # a comment", x=666)
    x = 666  # a comment

    >>> apply_flags("x = (1)", x=222)
    x = (222)

    >>> apply_flags("x = -(((1)))", x=222)
    x = 222

    >>> apply_flags("""x = -(
    ...
    ...     1
    ... )""", x=-11)
    x = -11

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

Using parens to define values that span lines:

    >>> apply_flags("""x = (
    ...
    ...        1
    ...     )
    ... """, x=12345)
    x = (
    <BLANKLINE>
           12345
        )

Using line continuations:

    >>> apply_flags("""x = \
    ... \
    ... 1
    ... """, x=True)
    x = True

An example containing multiple line-spanning assignments:

    >>> apply_flags("""x = y = '''Line 1
    ... Line 2
    ...
    ... Line 3
    ... ''' # a conmment
    ... for i in range(x):
    ...     print(i)
    ... z = \
    ... '''
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

    >>> logs.print_all()
    WARNING: error parsing Python source "'unterminated string": EOL
    while scanning string literal (<unknown>, line 1)

### Replace Regular Expression Matches

Flag values can be set in Notebook cells using `nb-replace` flag
attributes. `nb-replace` is a pattern that uses capture groups to
indicate where flag values should be inserted.

The `guild.plugins.nbexec._replace_flag_pattern_vals` function
implements the replacement logic.

    >>> from guild.plugins.nbexec import _replace_flag_pattern_vals

Helper function to apply replacement patterns.

    >>> def apply_patterns(src, **flags_and_repl):
    ...     flags = {
    ...         name: val
    ...         for name, val in flags_and_repl.items()
    ...         if not name.endswith("_repl")
    ...     }
    ...     flags_extra = {
    ...         name[:-5]: {"nb-replace": val}
    ...         for name, val in flags_and_repl.items()
    ...         if name.endswith("_repl")
    ...     }
    ...     state = _ApplyFlagsStateProxy(flags, flags_extra)
    ...     out = _replace_flag_pattern_vals(src, state)
    ...     print(out)

In the simplest case, the pattern matches the full flag assignment and
captures the value.

    >>> apply_patterns("x = 1", x=2, x_repl="x = (1)")
    x = 2

This can be generalized.

    >>> apply_patterns("x = 1", x=2, x_repl="x = (.+)")
    x = 2

If the pattern doesn't match, nothing is applied.

    >>> apply_patterns("x = 1", x=2, x_repl="x = (0)")
    x = 1

Regular expressions can be used inside and outside the capture groups
as needed.

    >>> apply_patterns("x = 22 # update me", x=33, x_repl="x\s*=\s*(.*) # update .*")
    x = 33 # update me

This pattern works on different variations of the source.

    >>> apply_patterns("x=22 # update me", x=33, x_repl="x\s*=\s*(.*) # update .*")
    x=33 # update me

    >>> apply_patterns("x = 11 # update here", x=33, x_repl="x\s*=\s*(.*) # update .*")
    x = 33 # update here

A non-capturing group can be used to match but not replace.

    >>> apply_patterns("x = 44", x=55, x_repl="(?:x|y) = (.*)")
    x = 55

Multiple groups can be used to include the flag value multiple times.

    >>> apply_patterns("""
    ... def f(a1="a1", a2="a2"):
    ...     print(a1, a2)
    ... """, x="hi", x_repl="a1=(\".*\"), a2=(\".*\")")
    def f(a1='hi', a2='hi'):
        print(a1, a2)

If a pattern doesn't define a capture group, the entire string is
replaced when matched.

    >>> apply_patterns("The value is 1234", x=4567, x_repl="1234")
    The value is 4567

Here we use several flag values with patterns.

    >>> apply_patterns("""
    ... x = 1  # flag:x
    ... y = 2  # flag:y
    ... print(x, y)  # x=1, y=2
    ... """,
    ... x=1.1234, x_repl=["x = (.+) # flag:x", "x=(1)"],
    ... y=2.2345, y_repl=["y = (.+) # flag:y", "y=(2)"])
    x = 1.1234 # flag:x
    y = 2.2345 # flag:y
    print(x, y)  # x=1.1234, y=2.2345

A pattern is only applied to the first match. Subsequent matches are
not replaced.

    >>> apply_patterns("x = 1, x = 2", x=3, x_repl="x = (\d+)")
    x = 3, x = 2

## IPython Magics

Guild converts all magics to valid Python code when processing cell
lines. The `nbexec` module's `_apply_flags_to_source_lines` function
handles this.

    >>> from guild.plugins.nbexec import _apply_flags_to_source_lines

Note that the lower level function `_replace_flag_assign_vals` does
not.

    >>> with LogCapture() as logs:
    ...     _replace_flag_assign_vals("%cd\n%pwd", _ApplyFlagsStateProxy({}, {})) # doctest: -NORMALIZE_PATHS
    '%cd\n%pwd'

    >>> logs.print_all()  # doctest: -NORMALIZE_PATHS
    WARNING: error parsing Python source '%cd\n%pwd': invalid syntax (<unknown>, line 1)

Using `_apply_flags_to_source_lines`:

    >>> _apply_flags_to_source_lines(
    ...     ["%cd ~\n", "%pwd"],
    ...     _ApplyFlagsStateProxy({}, {}))  # doctest: -PY2 -NORMALIZE_PATHS
    ["get_ipython().run_line_magic('cd', '~')\n", "get_ipython().run_line_magic('pwd', '')"]

Python 2:

    >>> _apply_flags_to_source_lines(
    ...     ["%cd ~\n", "%pwd"],
    ...     _ApplyFlagsStateProxy({}, {}))  # doctest: -PY3
    ["get_ipython().magic('cd ~')\n", "get_ipython().magic('pwd')"]

This works with flag assignments as well.

A helper function:

    >>> def apply_flags_to_lines(source, **flags):
    ...     lines = [line + "\n" for line in source.split("\n")]
    ...     state = _ApplyFlagsStateProxy(flags, {})
    ...     repl_lines = _apply_flags_to_source_lines(lines, state)
    ...     sys.stdout.write("".join(repl_lines))

Mixed code including magics:

    >>> apply_flags_to_lines("""
    ... %autoreload
    ... # A comment
    ... count = 1
    ... msg = "hi"
    ... !ls
    ... for _ in range(count):
    ...     print(msg)
    ... """, count=2, msg="hello")  # doctest: -NORMALIZE_WHITESPACE -PY2
    <BLANKLINE>
    get_ipython().run_line_magic('autoreload', '')
    # A comment
    count = 2
    msg = 'hello'
    get_ipython().system('ls')
    for _ in range(count):
        print(msg)

Python 2:

    >>> apply_flags_to_lines("""
    ... %autoreload
    ... # A comment
    ... count = 1
    ... msg = "hi"
    ... !ls
    ... for _ in range(count):
    ...     print(msg)
    ... """, count=2, msg="hello")  # doctest: -NORMALIZE_WHITESPACE -PY3
    <BLANKLINE>
    get_ipython().magic('autoreload')
    # A comment
    count = 2
    msg = 'hello'
    get_ipython().system('ls')
    for _ in range(count):
        print(msg)
    <BLANKLINE>
