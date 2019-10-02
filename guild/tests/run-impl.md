# Run impl tests

    >>> def run(cwd=".", **kw):
    ...     from guild import click_util
    ...     from guild.commands import run, run_impl2
    ...     ctx = run.run.make_context("", [])
    ...     ctx.params.update(kw)
    ...     args = click_util.Args(**ctx.params)
    ...     with SetCwd(cwd):
    ...         try:
    ...             run_impl2.main(args)
    ...         except SystemExit as e:
    ...             print(e.args[0])
    ...             print("<exit %i>" % e.args[1] if len(e.args) > 1 else 1)

    >>> def init_gf(s):
    ...     cwd = mkdtemp()
    ...     write(path(cwd, "guild.yml"), s)
    ...     return cwd

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

    >>> cwd = init_gf("invalid_guildfile_contents")
    >>> with LogCapture(stdout=True):
    ...     run(cwd)
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

    >>> cwd = init_gf("""
    ... - model: foo1
    ... - model: foo2
    ... """)

No default operation:

    >>> run(cwd)
    cannot find a default operation
    Try 'guild operations' for a list.
    <exit 1>

Can't find operation - no model spec):

    >>> run(cwd, opspec="foo")
    cannot find operation foo
    You may need to include a model in the form MODEL:OPERATION. Try
    'guild operations' for a list of available operations.
    <exit 1>

Can't find operation - model spec but no such model:

    >>> run(cwd, opspec="bar:foo")
    cannot find operation bar:foo
    Try 'guild operations' for a list of available operations.
    <exit 1>

Can't find operation - matched model but no such op:

    >>> run(cwd, opspec="foo1:bar")
    operation 'bar' is not defined for model 'foo1'
    Try 'guild operations foo1' for a list of available operations.
    <exit 1>

Multiple matching models:

    >>> run(cwd, opspec="foo:bar")
    there are multiple models that match 'foo'
    Try specifying one of the following:
      foo1
      foo2
    <exit 1>

## Invalid main flag reference

    >>> cwd = init_gf("""
    ... op:
    ...   main: ${foo}
    ... """)
    >>> run(cwd, opspec="op")
    invalid setting for operation 'op': main contains invalid reference 'foo'
    <exit 1>

## Invalid flag arg

    >>> cwd = init_gf("op: {}")
    >>> run(cwd, opspec="op", flags=["foo"])
    invalid argument 'foo' - expected NAME=VAL
    <exit 1>

## Model and op help

    >>> cwd = init_gf("""
    ... - model: m1
    ...   description: A sample model
    ...   operations:
    ...     op1:
    ...       description: Some op 1
    ...       flags:
    ...         foo: 1
    ...         bar:
    ...           description: Some flag bar
    ...           default: B
    ... """)

    >>> run(cwd, help_model=True)
    Usage: guild run [OPTIONS] m1:OPERATION [FLAG]...
    <BLANKLINE>
    A sample model
    <BLANKLINE>
    Use 'guild run m1:OPERATION --help-op' for help on a particular operation.
    <BLANKLINE>
    Operations:
      op1  Some op 1

    >>> run(cwd, help_op=True)
    Usage: guild run [OPTIONS] m1:op1 [FLAG]...
    <BLANKLINE>
    Some op 1
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      bar  Some flag bar (default is B)
      foo  (default is 1)

## == TODO =====================================================

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

- [ ] Flag args
  - [ ] Normal
  - [ ] Include batch files
  - [ ] Invalid
