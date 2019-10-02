# Run impl tests

    >>> def run(**kw):
    ...     from guild import click_util
    ...     from guild.commands import run, run_impl2
    ...     ctx = run.run.make_context("", [])
    ...     ctx.params.update(kw)
    ...     args = click_util.Args(**ctx.params)
    ...     try:
    ...         run_impl2.main(args)
    ...     except SystemExit as e:
    ...         print(e.args[0])
    ...         print("<exit %i>" % e.args[1] if len(e.args) > 1 else 1)

## Invalid arg combinations

    >>> run(opspec="foo", start="bar")
    OPERATION cannot be used with --start
    Try 'guild run --help' for more information.
    <exit 1>

    >>> run(opspec="foo", restart="bar")
    OPERATION cannot be used with --restart
    Try 'guild run --help' for more information.
    <exit 1>

## Invalid restart and start specs

    >>> guild_home = mkdtemp()

    >>> with SetGuildHome(guild_home):
    ...     run(restart="foo")
    could not find a run matching 'foo'
    Try 'guild runs list' for a list.
    <exit 1>

    >>> with SetGuildHome(guild_home):
    ...     run(start="bar")
    could not find a run matching 'bar'
    Try 'guild runs list' for a list.
    <exit 1>

## Invalid cwd Guild file

    >>> cwd = mkdtemp()
    >>> write(path(cwd, "guild.yml"), "invalid_guildfile_contents")

    >>> with SetCwd(cwd):
    ...     with LogCapture(stdout=True):
    ...         run()
    ERROR: error in ...guild.yml: invalid guildfile data
    'invalid_guildfile_contents': expected a mapping
    guildfile in '...' contains an error (see above for details)
    <exit 1>

## Invalid op spec

    >>> run(opspec="a/a/a")
    invalid operation spec 'a/a/a'
    Try 'guild operations' for a list of available operations.
    <exit 1>

## No matching model or operation

    >>> cwd = mkdtemp()
    >>> write(path(cwd, "guild.yml"), """
    ... - model: foo1
    ... - model: foo2
    ... """)

No default operation:

    >>> with SetCwd(cwd):
    ...     run()
    cannot find a default operation
    Try 'guild operations' for a list.
    <exit 1>

Can't find operation - no model spec):

    >>> with SetCwd(cwd):
    ...     run(opspec="foo")
    cannot find operation foo
    You may need to include a model in the form MODEL:OPERATION. Try
    'guild operations' for a list of available operations.
    <exit 1>

Can't find operation - model spec but no such model:

    >>> with SetCwd(cwd):
    ...     run(opspec="bar:foo")
    cannot find operation bar:foo
    Try 'guild operations' for a list of available operations.
    <exit 1>

Can't find operation - matched model but no such op:

    >>> with SetCwd(cwd):
    ...     run(opspec="foo1:bar")
    operation 'bar' is not defined for model 'foo1'
    Try 'guild operations foo1' for a list of available operations.
    <exit 1>

Multiple matching models:

    >>> with SetCwd(cwd):
    ...     run(opspec="foo:bar")
    there are multiple models that match 'foo'
    Try specifying one of the following:
      foo1
      foo2
    <exit 1>

## TODO

- [ ] Run script
- [ ] Run opdef
  - [ ] Default op
  - [ ] Named op, no modelspec
  - [ ] Model + op Guildfile
  - [ ] Just op package
  - [ ] Model + op package
  - [ ] Built-ins
- [ ] Restart run - can find opdef
  - [ ] No flag changes
  - [ ] Flag changes
- [ ] Restart run - can't find opdef
  - [ ] No flag changes
  - [ ] Flag changes (expect error)
