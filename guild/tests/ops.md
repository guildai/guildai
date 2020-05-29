# Operations

    >>> from guild import op as oplib

An operation is used to generate a run.

    >>> op = oplib.Operation()

Configure the operation as needed. In this case we specify command
args and a run directory.

    >>> op.cmd_args = [sys.executable, "-m", "guild.pass"]
    >>> op.run_dir = mkdtemp()

Run the operation without capturing output (tests rely on a spoofed
stdout to test output, which we don't want to interfere with).

    >>> with Env({"NO_RUN_OUTPUT": "1"}):
    ...     run, exit_code = oplib.run(op)

A successful run has an exit code of 0:

    >>> exit_code
    0

The run is generated in the specified run directory:

    >>> run.dir == op.run_dir, (run.dir, op.run_dir)
    (True, ...)

Generated files:

    >>> find(op.run_dir)
    .guild/attrs/cmd
    .guild/attrs/deps
    .guild/attrs/env
    .guild/attrs/exit_status
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/started
    .guild/attrs/stopped
    .guild/opref

## Staging a run

A run can be staged.

    >>> op.run_dir = mkdtemp()

    >>> run = oplib.stage(op)

Files for a staged run:

    >>> find(run.dir)
    .guild/ENV
    .guild/STAGED
    .guild/attrs/cmd
    .guild/attrs/deps
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/started
    .guild/opref

A staged run is denoted by a `STAGED` marker:

    >>> cat(run.guild_path("STAGED"))
    <empty>

## Operation callbacks

Callbacks are used to perform additional steps during operation
phases.

    >>> def init_output_summary_cb(op, run):
    ...     print("<initializing output summaries>")
    ...     return None

    >>> def run_initialized_cb(op, run):
    ...     print("<run initialized>")
    ...     run.write_attr("msg", "hello!")

    >>> op.callbacks = oplib.OperationCallbacks(
    ...     init_output_summary=init_output_summary_cb,
    ...     run_initialized=run_initialized_cb,
    ... )

Callbacks during stage:

    >>> op.run_dir = mkdtemp()
    >>> run = oplib.stage(op)
    <run initialized>

    >>> run.get("msg")
    'hello!'

Callbacks during run:

    >>> with Env({"NO_RUN_OUTPUT": "1"}):
    ...     run, exit_code = oplib.run(op)
    <run initialized>
