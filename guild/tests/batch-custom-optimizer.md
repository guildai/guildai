# Batch runs - custom optimizer

These tests illustrate the use of a custom optimizer.

As with the previous tests, we use the `batch` sample project:

    >>> project = sample("projects", "batch")

We'll run the `say.py` script with a `tune` optimizer. Any operation
may be specified as an optimizer. In this case, `tune` is an operation
defined in the project Guild file.

    >>> gf = guildfile.from_dir(project)
    >>> gf.default_model.get_operation("tune")
    <guild.guildfile.OpDef 'tune'>

For our tests, we'll use a new workspace:

    >>> workspace = mkdtemp()

And a helper for running ops:

    >>> from guild import _api as gapi

    >>> def run(op, optimizer=None):
    ...     out = gapi.run_capture_output(
    ...             op, optimizer=optimizer,
    ...             guild_home=workspace,
    ...             cwd=project)
    ...     print(out.strip())

Let's first run the `tune` operation directly:

    >>> run("tune")
    This script must be run as a Guild optimizer

Note this is run as a Guild operation and not as a Python script.

Now let's use the custom optimizer with `say.py`.

    >>> run("say.py", optimizer="tune")
    Tune using proto flags: [('loud', False), ('msg', 'hello')]

The generated runs:

    >>> from guild import op_util
    >>> with Chdir(project):
    ...     for run in gapi.runs_list(guild_home=workspace):
    ...         print(op_util.format_op_desc(run))
    say.py+tune
    tune
