# Run scripts

Guild can run scripts directly.

We'll use _api to run some examples.

    >>> from guild import _api as gapi

We'll use the `run-scripts` sample project:

    >>> project = sample("projects", "run-scripts")

Here are the files in the project:

    >>> for name in dir(project):
    ...   if not name.endswith(".pyc") and name != "__pycache__":
    ...     print(name)
    guild.yml
    say
    say.py
    say2
    say2.py

The Guild file:

    >>> gf = guildfile.from_dir(project)

The Guild file in this example uses an anonymous model to define
operations:

    >>> gf.models
    {'': <guild.guildfile.ModelDef ''>}
    >>> m = gf.default_model

The operations:

    >>> m.operations
    [<guild.guildfile.OpDef 'say2'>,
     <guild.guildfile.OpDef 'say2.py'>]

Note that the operations shadow scripts in the project. When running
an operation that is also a local file, Guild always uses the Guild
file operation.

Let's illustrate by running `say2`. Let's first note the `say2` exec
spec from the Guild file:

    >>> say2 = m.get_operation("say2")
    >>> say2.exec_
    'echo hello from guild file'

We'll bypass actually running the operation to save time. Instead
we'll print the command that would otherwise be run.

Here's a helper function for print the command for an operation:

    >>> def print_cmd(opspec):
    ...   import sys
    ...   output = gapi.run_capture_output(opspec, cwd=project, print_cmd=True)
    ...   output = output.replace(sys.executable, "python")
    ...   print(output.strip())

Here's the command for `say2`:

    >>> print_cmd("say2")
    echo hello from guild file

We see that the Guild file defined operation takes precedence over the
local `say2` script. In fact, the only way to run the `say2` locally
is to run it directly - Guild won't run it as long as `say2` is
defined for the anonymous model.

Let's run `say` now, which is not defined as an operation in the Guild
file:

    >>> print_cmd("say")
    /.../run-scripts/say

The same holds for `say2.py` and `say.py`:

    >>> print_cmd("say2.py")
    echo hello from guild file

    >>> print_cmd("say.py")
    python -um guild.op_main say
