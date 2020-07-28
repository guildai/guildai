# Help for operation

Guild prints operation help when the `--help-op` option is specified.

We use the `op-help` project to illustrate.

    >>> project = Project(sample("projects", "op-help"))

Use `help_op` to print help for the operation rather than run it:

    >>> project.run("op", help_op=True)  # doctest: +REPORT_UDIFF
    Usage: guild run [OPTIONS] op [FLAG]...
    <BLANKLINE>
    Sample operation
    <BLANKLINE>
    Another line of op description.
    <BLANKLINE>
    Use 'guild run --help' for a list of options.
    <BLANKLINE>
    Flags:
      c1  color choices (default is blue)
    <BLANKLINE>
          Choices:  red, blue, green
    <BLANKLINE>
      c2  number choices
    <BLANKLINE>
          Choices:
            1  2 minus 1
            2  1 plus 1
    <BLANKLINE>
      c3  aliases choices
    <BLANKLINE>
          Choices:
            a  option a
            b  option b
    <BLANKLINE>
      i   an int (default is 123)
      s   a string (required)
    <BLANKLINE>
          This is some more description...

                                       ^ workaround a mysterious
                                         issue with period at eol
                                         in example

Note that help is available even when a required flag is not
specified.

Similarly, help is available when other invalid flag values are
specified.

    >>> project.run("op", flags={"color": "orange"}, help_op=True)
    Usage: guild run [OPTIONS] op [FLAG]...
    ...

When `--help-op` is not specified, normal validation applies.

    >>> project.run("op", flags={"color": "orange"})
    guild: unsupported flag 'color'
    Try 'guild run op --help-op' for a list of flags or use --force-flags to skip this check.
    <exit 1>

    >>> project.run("op")
    Operation requires the following missing flags:
    <BLANKLINE>
      s  a string
    <BLANKLINE>
    Run the command again with these flags specified as NAME=VAL.
    <exit 1>

The op args:

    >>> project.run("op", flags={"s": "hi", "c3": "a"}, print_cmd=True)
    ??? -um guild.op_main guild.pass -- --c1 blue --c3 aaa --i 123 --s hi
