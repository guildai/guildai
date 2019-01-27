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

    >>> gf = guildfile.from_dir(project)

The anonymous model:

    >>> gf.models
    {'': <guild.guildfile.ModelDef ''>}

    >>> gf.default_model == gf.models[""]
    True

And its operations:

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef 'args'>,
     <guild.guildfile.OpDef 'globals'>]

We'll illustrate the various interfaces by running operations in a
temporary workspace.

    >>> workspace = mkdtemp()

And our run helper:

    >>> from guild import _api as gapi

    >>> def run(op, **flags):
    ...   out = gapi.run_capture_output(
    ...           op, cwd=project, guild_home=workspace,
    ...           flags=flags)
    ...   print(out.strip())

## Flags as args

Guild's command line argument interface is well documented throughout
the Guild tests. We'll demonstrate here however for completeness.

The `args` operation uses `args` for its flag dest:

    >>> args_op = gf.default_model.get_operation("args")
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

    >>> globals_op = gf.default_model.get_operation("globals")
    >>> globals_op.flags_dest
    'globals'

Let's run it:

    >>> run("args", i=4, f=4.321, b=False, s="yo yo yo")
    i: 4
    f: 4.321000
    s: yo yo yo
    b: False
