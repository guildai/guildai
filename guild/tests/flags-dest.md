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
     <guild.guildfile.OpDef 'params'>,
     <guild.guildfile.OpDef 'yml'>]

We'll illustrate the various interfaces by running operations in a
temporary workspace.

    >>> workspace = mkdtemp()

And our run helper:

    >>> from guild import _api as gapi

    >>> def run(op, **flags):
    ...   with Env({"NO_IMPORT_FLAGS_CACHE": "1",
    ...             "NO_IMPORT_FLAGS_PROGRESS": "1"}):
    ...       out = gapi.run_capture_output(
    ...               op, cwd=project, guild_home=workspace,
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

    >>> run("args", i=3, f=5.432, b=False, s="howdy")
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

    >>> run("args", i=4, f=4.321, b=False, s="yo yo yo")
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

    >>> run("params", i=5, s2="Whah")
    {'i': 5, 'strings': {'s1': 'Hola', 's2': 'Whah'}}

## Force args dest

If Guild can't detect that a script requires args, it assumes that the
flags interface is via globals unless flags imports is disabled.

If flags import is disabled and the script doesn't use argparse, the
Guild file can specify `args` as the flags dest.

    >>> run("args2", i=3)
    Global args: i=1 f=1.0
    Command line: ['.../.guild/sourcecode/args2.py', '--f', '2.2', '--i', '3']

The same script without an explicit `flags-dest` will default to using
"globals" in the case of the `args2.py` script.

    >>> run("args3", i=4)
    Global args: i=4 f=2.2
    Command line: ['.../.guild/sourcecode/args2.py']

## Handle two parsers

The `multi_argparse` module causes two parsers to be defined. Guild
should only read flags from the parser that calls `parse_args`.

    >>> run("multi_argparse.py")
    foo: 123
