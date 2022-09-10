# Filter runs

Runs can be filtered using a filter expression supported by
`guild.filter.` For details on filter expressions, see
[`filter-parser.md`](filter-parser.md) test.

The module `guild.filter_util` provides a function `filtered_runs`,
which applies a filter expression to a set of runs in a root
directory. The `filtered_runs` function mirrors `guild.var.runs()` but
applies the additional filter for a given expression.

    >>> from guild.filter_util import filtered_runs

## Sample runs

For our tests we use the set of runs in the `filter-runs` sample
directory.

    >>> runs_root = sample("filter-runs")

Here's the default list of runs for the sample root:

    >>> from guild import var
    >>> runs = var.runs(runs_root)
    >>> runs
    [<guild.run.Run 'e394b696ea204ade95ca29e4b868fdf9'>,
     <guild.run.Run 'a5520d132b4148a5bad3c4f795b7c362'>,
     <guild.run.Run '2dc1529ba06c46fda486395a61475dbe'>,
     <guild.run.Run '79ca9e64e4d7453f999a6bbd1e7c03f0'>,
     <guild.run.Run 'fe83a924ae144693a72b420962a7d9d1'>]

    >>> print_runs(runs, short_ids=True, labels=True, flags=True, scalars=True)
    util:test  e394b696  target=fe83a924ae144693a72b420962a7d9d1  target=fe83a924   loss=0.52803
    util:test  a5520d13  target=2dc1529ba06c46fda486395a61475dbe  target=2dc1529b   loss=0.47875
    train      2dc1529b  noise=0.1 x=1.1                          noise=0.1 x=1.1   loss=0.47875
    train      79ca9e64  noise=0.1 x=0.1                          noise=0.1 x=0.1   loss=0.43514
    train      fe83a924  noise=0.1 x=-1.0                         noise=0.1 x=-1.0  loss=0.52803

## Filtering runs

When filtering runs, we can specify a run index to lookup run
values. By default, `filter_runs` uses a run index configured to cache
data in the default runs cache directory (located under Guild home
`cache/runs`). For these tests, we create an index that caches data in
a temp directory.

    >>> from guild.index import RunIndex

    >>> index = RunIndex(mkdtemp())

Here's a function we can use to filter and print runs for a specified
filter expression.

    >>> def filter(expr, sort=None, base_filter=None, **print_kw):
    ...     runs = filtered_runs(
    ...         expr,
    ...         root=runs_root,
    ...         sort=sort,
    ...         base_filter=base_filter,
    ...         index=index)
    ...     if runs:
    ...         print_runs(runs, short_ids=True, **print_kw)
    ...     else:
    ...         print("<empty>")

### Empty filter expressions

If a filter is unspecified, the behavior of
`guild.filter_util.filtered_runs()` is identical to that of
`guild.var.runs()`.

    >>> filter(None)
    util:test  e394b696
    util:test  a5520d13
    train      2dc1529b
    train      79ca9e64
    train      fe83a924

    >>> filter("")
    util:test  e394b696
    util:test  a5520d13
    train      2dc1529b
    train      79ca9e64
    train      fe83a924

### Terms

While not related to runs, the filter expression language supports
evaluation using boolean, numeric, and text terms.

    >>> filter("true")
    util:test  e394b696
    util:test  a5520d13
    train      2dc1529b
    train      79ca9e64
    train      fe83a924

    >>> filter("false")
    <empty>

    >>> filter("true or false")
    util:test  e394b696
    util:test  a5520d13
    train      2dc1529b
    train      79ca9e64
    train      fe83a924

    >>> filter("1")
    util:test  e394b696
    util:test  a5520d13
    train      2dc1529b
    train      79ca9e64
    train      fe83a924

    >>> filter("0")
    <empty>

    >>> filter("cat")
    util:test  e394b696
    util:test  a5520d13
    train      2dc1529b
    train      79ca9e64
    train      fe83a924

### Run attributes

    >>> filter("id contains e39")
    util:test  e394b696

    >>> filter("not id contains e39")
    util:test  a5520d13
    train      2dc1529b
    train      79ca9e64
    train      fe83a924

    >>> filter("op = train")
    train  2dc1529b
    train  79ca9e64
    train  fe83a924

    >>> filter("op != train")
    util:test  e394b696
    util:test  a5520d13

    >>> filter("model = ''")
    train  2dc1529b
    train  79ca9e64
    train  fe83a924

    >>> filter("model = util")
    util:test  e394b696
    util:test  a5520d13

### Run flags

    >>> filter("noise = 0.1", flags=True)
    train  2dc1529b  noise=0.1 x=1.1
    train  79ca9e64  noise=0.1 x=0.1
    train  fe83a924  noise=0.1 x=-1.0

    >>> filter("noise = 0.1 and x > 0.1", flags=True)
    train  2dc1529b  noise=0.1 x=1.1

    >>> filter("noise = 0.1 or x > 0.1", flags=True)
    train  2dc1529b  noise=0.1 x=1.1
    train  79ca9e64  noise=0.1 x=0.1
    train  fe83a924  noise=0.1 x=-1.0

    >>> filter("op = train and x in [1.1,0.1,0.2]", flags=True)
    train  2dc1529b  noise=0.1 x=1.1
    train  79ca9e64  noise=0.1 x=0.1

    >>> filter("op = train and x not in [1.1,0.1,0.2]", flags=True)
    train  fe83a924  noise=0.1 x=-1.0

### Run scalars

    >>> filter("loss >= 0.5", scalars=True)
    util:test  e394b696  loss=0.52803
    train      fe83a924  loss=0.52803

    >>> filter("flag:x is undefined", flags=True)
    util:test  e394b696  target=fe83a924ae144693a72b420962a7d9d1
    util:test  a5520d13  target=2dc1529ba06c46fda486395a61475dbe

    >>> filter("flag:x is not undefined", flags=True)
    train  2dc1529b  noise=0.1 x=1.1
    train  79ca9e64  noise=0.1 x=0.1
    train  fe83a924  noise=0.1 x=-1.0

    >>> filter("flag:xxx is undefined", flags=True)
    util:test  e394b696  target=fe83a924ae144693a72b420962a7d9d1
    util:test  a5520d13  target=2dc1529ba06c46fda486395a61475dbe
    train      2dc1529b  noise=0.1 x=1.1
    train      79ca9e64  noise=0.1 x=0.1
    train      fe83a924  noise=0.1 x=-1.0

    >>> filter("flag:xxx is not undefined", flags=True)
    <empty>

### Multi-type filters

All runs with scalars for reference:

    >>> filter("true", scalars=True)
    util:test  e394b696  loss=0.52803
    util:test  a5520d13  loss=0.47875
    train      2dc1529b  loss=0.47875
    train      79ca9e64  loss=0.43514
    train      fe83a924  loss=0.52803

Filter runs by loss:

    >>> filter("loss > 0.5", scalars=True)
    util:test  e394b696  loss=0.52803
    train      fe83a924  loss=0.52803

    >>> filter("loss <= 0.5", scalars=True)
    util:test  a5520d13  loss=0.47875
    train      2dc1529b  loss=0.47875
    train      79ca9e64  loss=0.43514

    >>> filter("loss >= .45 and loss < 0.5")
    util:test  a5520d13
    train      2dc1529b

    >>> filter("loss > 0.5 and foo < 3", scalars=True)
    <empty>

    >>> filter("loss > 0.5 and foo is undefined", scalars=True)
    util:test  e394b696  loss=0.52803
    train      fe83a924  loss=0.52803

Note that `loss` is a valid scalar tag in both `train` and `util:test`
operations. We can limit the result by specifying the operation we
want to filter on.

    >>> filter("loss > 0.5 and op = train", scalars=True)
    train  fe83a924  loss=0.52803

We can also include the scalar prefix associated with the test loss
('target/.guild') to filter by the whole scalar key.

    >>> filter("target/.guild#loss > 0.5", scalars=True)
    util:test  e394b696  loss=0.52803

### No match filters

Non existing run values:

    >>> filter("no-such-value < hello")
    <empty>

## Invalid filter rsyntax

Syntax errors propogate as exceptions.

    >>> filter("and id = foo")
    Traceback (most recent call last):
    SyntaxError: Syntax error at line 1, pos 0: unexpected token 'and'

## Pre-parsed filters

A filter may be pre-parsed using the parsing facility in
`guild.filter`.

    >>> from guild import filter as filterlib

    >>> parser = filterlib.parser()
    >>> parse = lambda expr: parser.parse(expr)

    >>> filter(parse("true"))
    util:test  e394b696
    util:test  a5520d13
    train      2dc1529b
    train      79ca9e64
    train      fe83a924

### Index refresh types

A parsed filter may provide a list of index refresh types for a given
filter. This is useful to skip refresh types that aren't part of a
filter. For example, scalars require reading potentially large TF
event files, which can add time to a filter. If a filter doesn't need
to read scalars, it can omit the scalars from the list of refresh
types.

    >>> def parse_with_refresh_types(expr, refresh_types):
    ...     f = parse(expr)
    ...     f.index_refresh_types = refresh_types
    ...     return f

Note that once a filter is refreshed for a particular type for a run,
it will reuse cached values. To illustrate how refresh types are used,
we need a fresh index.

    >>> index = RunIndex(mkdtemp())

If we omit a required refresh type, that type is not supported. Here's
a filter that requires run attrs but does not specify attributes in
the required types.

    >>> filter(parse_with_refresh_types("op = train", []))
    <empty>

When we specify that attributes are required, the filter works as
expected.

    >>> filter(parse_with_refresh_types("op = train", ["attr"]))
    train  2dc1529b
    train  79ca9e64
    train  fe83a924

Now that the index is refreshed with attributes, filters that need
attributes succeed even when they don't include attributes in the
refresh types.

    >>> filter(parse_with_refresh_types("op = train", []))
    train  2dc1529b
    train  79ca9e64
    train  fe83a924

    >>> filter(parse_with_refresh_types("short_id = e394b696", []))
    util:test  e394b696

They do not yet support flags.

    >>> filter(parse_with_refresh_types("noise = 0.1", []), flags=True)
    <empty>

We must provide the required refresh type.

    >>> filter(parse_with_refresh_types("noise = 0.1", ["flag"]), flags=True)
    train  2dc1529b  noise=0.1 x=1.1
    train  79ca9e64  noise=0.1 x=0.1
    train  fe83a924  noise=0.1 x=-1.0

## Future work

### Additional filters

Run selection filters only support selection using attributes, flags,
and scalars. The do not provide equivalent filter support for:

- Tags
- Comments
- Start date/time (time range specs)

Support for this run information may be provided in future releases.
