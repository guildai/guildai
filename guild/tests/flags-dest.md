# Flags dest

By default, Guild applies flag values to Python main modules using
command line arguments.

A Guild run command like this:

    $ guild run train epochs=100

typically is translated to a call to a module that includes the
command line arguments:

    --epochs 100

Guild can also apply flags as global variables to Python modules.

For example, the same Guild run command could set a global variable
`epochs` in the main module.

We'll use the sample project `flags-dest` to illustrate.

    >>> project = sample("projects", "flags-dest")

This project uses a Guild file with an anonymous model to define
operations that we can test.

    >>> gf = guildfile.for_dir(project)

The anonymous model:

    >>> gf.models
    {'': <guild.guildfile.ModelDef ''>}

    >>> gf.default_model == gf.models[""]
    True

And its operations:

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef 'args'>,
     <guild.guildfile.OpDef 'args2'>,
     <guild.guildfile.OpDef 'args3'>,
     <guild.guildfile.OpDef 'globals'>,
     <guild.guildfile.OpDef 'no-dest'>,
     <guild.guildfile.OpDef 'params'>,
     <guild.guildfile.OpDef 'params-dict'>,
     <guild.guildfile.OpDef 'params-namespace'>,
     <guild.guildfile.OpDef 'split-args'>,
     <guild.guildfile.OpDef 'split-globals'>,
     <guild.guildfile.OpDef 'split-typed'>]

We'll illustrate the various interfaces by running operations in a
temporary workspace.

    >>> workspace = mkdtemp()

And our run helper:

    >>> from guild import _api as gapi

    >>> def guild_run(op=None, force_flags=False, print_cmd=False, stage=False,
    ...         start=None, **flags):
    ...   with Env({"NO_IMPORT_FLAGS_CACHE": "1",
    ...             "NO_IMPORT_FLAGS_PROGRESS": "1"}):
    ...       out = gapi.run_capture_output(
    ...               op, cwd=project, guild_home=workspace,
    ...               force_flags=force_flags,
    ...               print_cmd=print_cmd,
    ...               stage=stage,
    ...               start=start,
    ...               flags=flags)
    ...       print(out.strip())

## Flags as args

Guild's command line argument interface is well documented throughout
the Guild tests. We'll demonstrate here however for completeness.

The `args` operation uses `args` for its flag dest:

    >>> args_op = gf.default_model["args"]
    >>> args_op.flags_dest
    'args'

It's target main module, `args.py` parses command line args and prints
out the flag values.

Lets run the operation:

    >>> guild_run("args", i=3, f=5.432, b=False, s="howdy")
    i: 3
    f: 5.432000
    s: howdy
    b: False

## Globals

The `globals` operation specifies `globals` for the flags dest:

    >>> globals_op = gf.default_model["globals"]
    >>> globals_op.flags_dest
    'globals'

Let's run it:

    >>> guild_run("args", i=4, f=4.321, b=False, s="yo yo yo")
    i: 4
    f: 4.321000
    s: yo yo yo
    b: False

## Global dict

Guild supports setting flags as items of a global dict.

The `params` operations specifies `global:params` as the flags dest.

    >>> params_op = gf.default_model["params"]
    >>> params_op.flags_dest
    'global:params'

Let's run it:

    >>> guild_run("params", i=5, s2="Whah")
    {'f': {'a': 1.123, 'b': 2.234},
     'i': 5,
     'l': [1, 2, 'foo'],
     'strings': {'s1': 'Hola', 's2': 'Whah'}}

And again with an encoded list flag:

    >>> guild_run("params", i=2, l="2 3 bar baz")
    {'f': {'a': 1.123, 'b': 2.234},
     'i': 2,
     'l': [2, 3, 'bar', 'baz'],
     'strings': {'s1': 'Hola'}}

## Alt global dict

The `params-dict` operation is the same operation def as `params` but
uses the `dict:<name>` flags dest. This is equivalent to
`global:<name>`.

    >>> params_dict_op = gf.default_model["params-dict"]
    >>> params_dict_op.flags_dest
    'dict:params'

Run it:

    >>> guild_run("params-dict", i=5, s2="Whah")
    {'f': {'a': 1.123, 'b': 2.234},
     'i': 5,
     'l': [1, 2, 'foo'],
     'strings': {'s1': 'Hola', 's2': 'Whah'}}

And again with an encoded list flag:

    >>> guild_run("params-dict", i=2, l="2 3 bar baz")
    {'f': {'a': 1.123, 'b': 2.234},
     'i': 2,
     'l': [2, 3, 'bar', 'baz'],
     'strings': {'s1': 'Hola'}}

## Global namespace

The `params-namespace` operation uses a `SimpleNamespace` instead of a
`dict`.

    >>> params_namespace_op = gf.default_model["params-namespace"]
    >>> params_namespace_op.flags_dest
    'namespace:params'

Run it:

    >>> guild_run("params-namespace", b=1, f=2.234, s="hi", l="2 3 bar")
    namespace(b=True, f=2.234, i=2, l=[2, 3, 'bar'], s='hi')

## Force args dest

If Guild can't detect that a script requires args, it assumes that the
flags interface is via globals unless flags imports is disabled.

If flags import is disabled and the script doesn't use argparse, the
Guild file can specify `args` as the flags dest.

    >>> guild_run("args2", i=3)
    Global args: i=1 f=1.0
    Command line: ['.../.guild/sourcecode/args2.py', '--f', '2.2', '--i', '3']

The same script without an explicit `flags-dest` will default to using
"globals" in the case of the `args2.py` script.

    >>> guild_run("args3", i=4)
    Global args: i=4 f=2.2
    Command line: ['.../.guild/sourcecode/args2.py']

## Handle two parsers

The `multi_argparse` module causes two parsers to be defined. Guild
should only read flags from the parser that calls `parse_args`.

    >>> guild_run("multi_argparse.py")
    foo: 123

## Additional global tests

Guild only changes the initial value of a flag. The `globals2.py`
script sets alternative values for flags based on initial
values. Subsequent setting of flag values are not affected by Guild.

    >>> guild_run("globals2.py")
    1 2

    >>> guild_run("globals2.py", i=2)
    3 4

    >>> guild_run("globals2.py", i=3)
    33 44

Guild does not consider `j` to be a flag because its assignment is not
a constant.

    >>> guild_run("globals2.py", j=1)
    Traceback (most recent call last):
    RunError: ...unsupported flag 'j'...

    >>> guild_run("globals2.py", j=1, force_flags=True)
    1 1

Subsequent mods to `j` apply as well.

    >>> guild_run("globals2.py", i=2, j=1, force_flags=True)
    3 4

## Splitting flag args

The `arg-split` flag attribute is used to split a flag assignment into
a list of values. This list is applied either as a series of arguments
to the long form option in the case of `args` dest or as a Python list
in the case of `globals` dest.

### Splitting for args

The `split-args` operation illustrates the case where dest is `args`.

In the default case, no args are provided.

    >>> guild_run("split-args")
    ['1', '2', 'a b']
    [1, 2, 3]

The `x` flag is split using the default shlex parser.

    >>> guild_run("split-args", x="1 2 'hello there'")
    ['1', '2', 'hello there']
    [1, 2, 3]

The `y` flag is split using the `,` char.

    >>> guild_run("split-args", y="4,5,6")
    ['1', '2', 'a b']
    [4, 5, 6]

Here's the underlying command:

    >>> guild_run("split-args", x="1 2 'hello there'", y="1,2,3", print_cmd=True)
    ??? -um guild.op_main args3 -- --x 1 2 'hello there' --y 1 2 3

Next we confirm that we can stage an operation with a flag arg split
and start it. This verifies that we correctly save the flag info with
the staged run.

    >>> guild_run("split-args", x="1 2 'hello there'", y="1,2", stage=True)
    split-args staged as ...
    To start the operation, use 'guild run --start ...'

    >>> latest_run_id = gapi.runs_list(cwd=project, guild_home=workspace)[0].id

Start the run:

    >>> guild_run(start=latest_run_id)
    ['1', '2', 'hello there']
    [1, 2]

Guild detects the use of `nargs='+'` in the argparse argument and
automatically sets `arg-split` to True so that this works when running
the script directly. As the default behavior requires shlex syntax,
our example above doesn't work with `args3.py`.

    >>> guild_run("args3.py", x="1 2 foo", y="2,1")
    Traceback (most recent call last):
    RunError: ...args3.py: error: argument --y: invalid int value: '2,1'...

When we use the expected syntax:

    >>> guild_run("args3.py", x="1 2 foo", y="2 1")
    ['1', '2', 'foo']
    [2, 1]

### Splitting for globals

The `split-globals` operation shows how split flag values are applied
to globals.

In the default case, .

    >>> guild_run("split-globals")
    [1, 2, 3]
    []

Here's the underlying command:

    >>> guild_run("split-globals", print_cmd=True)
    ??? -um guild.op_main globals3 -- --x '[1, 2, 3]' --y '[]'

The `x` flag is split using the default shlex parser.

    >>> guild_run("split-globals", x="1 2 'hello there'")
    [1, 2, 'hello there']
    []

The `y` flag is split using the `:` char.

    >>> guild_run("split-globals", y="1:2:three")
    [1, 2, 3]
    [1, 2, 'three']

Here's the underlying command:

    >>> guild_run("split-globals", x="1 2 'hello there'", y="1:2:three", print_cmd=True)
    ??? -um guild.op_main globals3 -- --x '[1, 2, hello there]' --y '[1, 2, three]'

Stage and start a run to verify that we save arg split information
correctly in the case of globals dest.

    >>> guild_run("split-globals", x="1 2 'hello there' yes", y="1:2:three:no", stage=True)
    split-globals staged as ...
    To start the operation, use 'guild run --start ...'

    >>> latest_run_id = gapi.runs_list(cwd=project, guild_home=workspace)[0].id

    >>> guild_run(start=latest_run_id)
    [1, 2, 'hello there', True]
    [1, 2, 'three', False]

Specify a single value for each flag. This shows that we convey a list
containing the value rather than the value itself.

    >>> guild_run("split-globals", x="hello", y="1")
    ['hello']
    [1]

Running the script directly:

    >>> guild_run("globals3.py", x="1 2.2", y="foo bar yes 3")
    [1, 2.2]
    ['foo', 'bar', True, 3]

    >>> guild_run("globals3.py", x="hello", y="1")
    ['hello']
    [1]

### Splitting and flag type

Guild applies flag type to each part of a split flag value.

    >>> guild_run("split-typed", paths=". subdir", ints="1 2 3")
    ['.../guild/tests/samples/projects/flags-dest',
     '.../guild/tests/samples/projects/flags-dest/subdir']
    [1, 2, 3]

### Arg splitting and batches

    >>> guild_run("split-args", x=["a b", "c 'd e'"], y=["1,2"])
    INFO: [guild] Running trial ...: split-args (x='a b', y=1,2)
    ['a', 'b']
    [1, 2]
    INFO: [guild] Running trial ...: split-args (x="c 'd e'", y=1,2)
    ['c', 'd e']
    [1, 2]

## No flags interface

Use `none` for flags dests to skip the application of flags. This is
useful when the main spec assumes responsibility for all of the
command arguments.

    >>> guild_run("no-dest", x="123", y="abc")

## Flag Imports

Below we test imports based on flags dest and import settings using
the `--help-op` option.

    >>> cd(project)

    >>> run("guild run args --help-op")
    Usage: guild run [OPTIONS] args [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      b  (default is no)
      f  (default is 2.345)
      i  (default is 2)
      s  (default is hi)
    <exit 0>

    >>> run("guild run globals --help-op")
    Usage: guild run [OPTIONS] globals [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      b  (default is no)
      f  (default is 2.345)
      i  (default is 2)
      s  (default is hi)
    <exit 0>

    >>> run("guild run params --help-op")
    Usage: guild run [OPTIONS] params [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      f.a  (default is 1.123)
      f.b  (default is 2.234)
      i    (default is 2)
      l    (default is 1 2 foo)
      s1   (default is Hola)
      s2
    <exit 0>

    >>> run("guild run args2 --help-op")
    Usage: guild run [OPTIONS] args2 [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      f  (default is 2.2)
      i  (default is 2)
    <exit 0>

    >>> run("guild run args3 --help-op")
    Usage: guild run [OPTIONS] args3 [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      f  (default is 2.2)
      i  (default is 2)
    <exit 0>

    >>> run("guild run split-args --help-op")
    Usage: guild run [OPTIONS] split-args [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      x  (default is 1 2 'a b')
      y  (default is 1,2,3)
    <exit 0>

    >>> run("guild run split-globals --help-op")
    Usage: guild run [OPTIONS] split-globals [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      x  (default is 1 2 3)
      y  (default is '')
    <exit 0>

    >>> run("guild run split-typed --help-op")
    Usage: guild run [OPTIONS] split-typed [FLAG]...
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      ints
      paths
    <exit 0>
