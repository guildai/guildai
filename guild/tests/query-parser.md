# Query parser

Parsing support is provided by `guild.query.qparse`:

    >>> from guild.query import qparse

A parser and parse function:

    >>> parser = qparse.parser()
    >>> p = parser.parse

## Selecting scalars

By default, selected columns are considered to be scalars:

    >>> p("select loss")
    <guild.query.Select ['scalar:loss']>

They can alternatively be explicitly prefixed:

    >>> p("select scalar:loss")
    <guild.query.Select ['scalar:loss']>

Here's a list of scalars:

    >>> p("select loss, train_acc, val_acc")
    <guild.query.Select
      ['scalar:loss',
       'scalar:train_acc',
       'scalar:val_acc']>

A scalar may contain a qualifier (min, max, first, or last):

    >>> p("select min loss")
    <guild.query.Select ['scalar:min loss']>

    >>> p("select max loss")
    <guild.query.Select ['scalar:max loss']>

    >>> p("select first loss")
    <guild.query.Select ['scalar:first loss']>

    >>> p("select last loss")
    <guild.query.Select ['scalar:last loss']>

    >>> p("select avg gpu")
    <guild.query.Select ['scalar:avg gpu']>

    >>> p("select total hits")
    <guild.query.Select ['scalar:total hits']>

    >>> p("select count loss")
    <guild.query.Select ['scalar:count loss']>

A scalar step may be specified by adding 'step' after the scalar:

    >>> p("select loss step")
    <guild.query.Select ['scalar:loss step']>

Here's a select query that summarizes a run in terms of loss and
accuracy:

    >>> p("""
    ...   select min loss,
    ...          min loss step,
    ...          max acc,
    ...          max acc step,
    ...          last loss step
    ... """)
    <guild.query.Select
      ['scalar:min loss',
       'scalar:min loss step',
       'scalar:max acc',
       'scalar:max acc step',
       'scalar:last loss step']>

Wildcards may be specified to match multiple scalar keys:

    >>> p("select losses/.+")
    <guild.query.Select ['scalar:losses/.+']>

### Selecting attributes

Run attributes must be prefixed with a dot ('.') or with the full
prefix 'attr:'.

    >>> p("select .id")
    <guild.query.Select ['attr:id']>

    >>> p("select attr:id")
    <guild.query.Select ['attr:id']>

A list of selected attributes:

    >> p("select .id, .started, .stopped, .time")
    <guild.query.Select
      ['attr:id',
       'attr:started',
       'attr:stopped',
       'attr:time']>

### Selecting flags

Flags may be selected by either using an equals size ('='):

    >>> p("select =learning-rate, =batch-size")
    <guild.query.Select ['flag:learning-rate', 'flag:batch-size']>

or by explicitly using the 'flag:' prefix:

    >>> p("select flag:learning-rate, flag:batch-size")
    <guild.query.Select ['flag:learning-rate', 'flag:batch-size']>

### Specifying column names

Any column may be named using 'AS NAME' syntax.

    >>> p("select last loss step as steps")
    <guild.query.Select ['scalar:last loss step as steps']>

Other examples:

    >>> p("select =learning-rate as 'Learning Rate'")
    <guild.query.Select ["flag:learning-rate as 'Learning Rate'"]>

    >>> p("select .id, =batch-size, train/losses/total_loss as loss")
    <guild.query.Select
      ['attr:id',
       'flag:batch-size',
       'scalar:train/losses/total_loss as loss']>

### Edge cases and errors

Quoting:

    >>> p("select 'loss'")
    <guild.query.Select ['scalar:loss']>

    >>> p("select 'foo bar baz'")
    <guild.query.Select ['scalar:foo bar baz']>

Strange but legal regex:

    >>> p("select 'losses/[^ ,]', acc")
    <guild.query.Select ['scalar:losses/[^ ,]', 'scalar:acc']>

Any quoted column spec is treated as a scalar:

    >>> p("select 'flag:batch-size'")
    <guild.query.Select ['scalar:flag:batch-size']>

Empty query string:

    >>> p("")
    Traceback (most recent call last):
    ParseError: query string cannot be empty

Unsupported syntax:

    >>> p("insert into flags")
    Traceback (most recent call last):
    ParseError: unexpected token 'insert', line 1, pos 0

Unsupported col type:

    >>> p("select flags:foo")
    <guild.query.Select ['scalar:flags:foo']>

NOTE: This message is far from ideal. Our parser should balk at the
invalid prefix. There is an ordering problem with the parser.

Unsupported scalar qualifier:

    >>> p("select minn loss")
    Traceback (most recent call last):
    ParseError: unexpected token 'loss', line 1, pos 12

Using a scalar qualifiers as a name (don't need to quote):

    >>> p("select min loss as min")
    <guild.query.Select ['scalar:min loss as min']>

    >>> p("select min loss step as step")
    <guild.query.Select ['scalar:min loss step as step']>
