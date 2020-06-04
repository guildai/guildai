# Flag Values

These tests illustrate how Guild conveys flag values from both
configuration (Guild files) and user specified values on the command
line.

Related tests: [quoted-flag-vals](quoted-flag-vals.md).

We'll use the `flag-vals` project:

    >>> project = Project(sample("projects", "flag-vals"))

Let's start by running a couple operations - one that passes values as
command line arguments (`args`) and another that sets Python global
variables (`globals`).

## Passing values as arguments

First, the `args` operation. Here's are the default flag values for
the operation:

    >>> gf = guildfile.for_dir(project.cwd)

    >>> pprint(gf.default_model.get_operation("args").flag_values())
    {'b1': True,
     'b2': False,
     'f1': 1.1,
     'f2': 1.0,
     'f3': 0.1,
     'f4': 12300.0,
     'f5': -6.78e-07,
     'f6': 6543210.0,
     'i': 456,
     's1': 'a',
     's2': 'a b',
     's3': '123e4',
     's4': '-0.00034',
     's5': ''}

Here's the output for the default values:

    >>> project.run("args")
    --b1 '1'
    --b2 ''
    --f1 '1.1'
    --f2 '1.0'
    --f3 '0.1'
    --f4 '12300.0'
    --f5 '-6.78e-07'
    --f6 '6543210.0'
    --i '456'
    --s1 'a'
    --s2 'a b'
    --s3 '123e4'
    --s4 '-0.00034'
    --s5 ''

We can change the values at the run command:

    >>> project.run("args", flags={
    ...   "b1": False,
    ...   "b2": True,
    ...   "s3": "hello",
    ...   "s4": None,
    ...   "f4": "there",
    ... })
    --b1 ''
    --b2 '1'
    --f1 '1.1'
    --f2 '1.0'
    --f3 '0.1'
    --f4 'there'
    --f5 '-6.78e-07'
    --f6 '6543210.0'
    --i '456'
    --s1 'a'
    --s2 'a b'
    --s3 'hello'
    --s5 ''

Note that `--s4` does not appear because the flag value is None.

## Passing arguments as globals

The `globals` operation passes the same set of flags to its script via
a `params` global variable.

Here are the default values for the `globals` operation (they're the
same as the `args` flags):

    >>> pprint(gf.default_model.get_operation("globals").flag_values())
    {'b1': True,
     'b2': False,
     'f1': 1.1,
     'f2': 1.0,
     'f3': 0.1,
     'f4': 12300.0,
     'f5': -6.78e-07,
     'f6': 6543210.0,
     'i': 456,
     's1': 'a',
     's2': 'a b',
     's3': '123e4',
     's4': '-0.00034',
     's5': ''}

And the run output:

    >>> project.run("globals")
    b1: True
    b2: False
    f1: 1.1
    f2: 1.0
    f3: 0.1
    f4: 12300.0
    f5: -6.78e-07
    f6: 6543210.0
    i: 456
    s1: 'a'
    s2: 'a b'
    s3: '123e4'
    s4: '-0.00034'
    s5: ''

And with modified flags:

    >>> project.run("globals", flags={
    ...   "b1": False,
    ...   "b2": True,
    ...   "s3": "hello",
    ...   "s4": None,
    ...   "f4": "there",
    ... })
    b1: False
    b2: True
    f1: 1.1
    f2: 1.0
    f3: 0.1
    f4: 'there'
    f5: -6.78e-07
    f6: 6543210.0
    i: 456
    s1: 'a'
    s2: 'a b'
    s3: 'hello'
    s5: ''

## Flag list values

Flag list values drive batch trials.

Here's the `args-batch` flags. Note the addition of `l`, which is a
list.

    >>> pprint(gf.default_model.get_operation("args-batch").flag_values())
    {'b1': True,
     'b2': False,
     'f1': 1.1,
     'f2': 1.0,
     'f3': 0.1,
     'f4': 12300.0,
     'f5': -6.78e-07,
     'f6': 6543210.0,
     'i': 456,
     'l': [1, 2.3, 'foo'],
     's1': 'a',
     's2': 'a b',
     's3': '123e4',
     's4': '-0.00034',
     's5': ''}

When we run this operation, it generates three trials:

    >>> project.run("args-batch") # doctest: +REPORT_UDIFF
    INFO: [guild] Running trial ...: args-batch
          (b1=yes, b2=no, f1=1.1, f2=1.0, f3=0.1, f4=12300.0, f5=-6.78e-07,
           f6=6543210.0, i=456, l=1, s1=a, s2='a b', s3='123e4', s4='-0.00034',
           s5='')
    --b1 '1'
    --b2 ''
    --f1 '1.1'
    --f2 '1.0'
    --f3 '0.1'
    --f4 '12300.0'
    --f5 '-6.78e-07'
    --f6 '6543210.0'
    --i '456'
    --l '1'
    --s1 'a'
    --s2 'a b'
    --s3 '123e4'
    --s4 '-0.00034'
    --s5 ''
    INFO: [guild] Running trial ...: args-batch
          (b1=yes, b2=no, f1=1.1, f2=1.0, f3=0.1, f4=12300.0, f5=-6.78e-07,
           f6=6543210.0, i=456, l=2.3, s1=a, s2='a b', s3='123e4', s4='-0.00034',
           s5='')
    --b1 '1'
    --b2 ''
    --f1 '1.1'
    --f2 '1.0'
    --f3 '0.1'
    --f4 '12300.0'
    --f5 '-6.78e-07'
    --f6 '6543210.0'
    --i '456'
    --l '2.3'
    --s1 'a'
    --s2 'a b'
    --s3 '123e4'
    --s4 '-0.00034'
    --s5 ''
    INFO: [guild] Running trial ...: args-batch
          (b1=yes, b2=no, f1=1.1, f2=1.0, f3=0.1, f4=12300.0, f5=-6.78e-07,
           f6=6543210.0, i=456, l=foo, s1=a, s2='a b', s3='123e4', s4='-0.00034',
           s5='')
    --b1 '1'
    --b2 ''
    --f1 '1.1'
    --f2 '1.0'
    --f3 '0.1'
    --f4 '12300.0'
    --f5 '-6.78e-07'
    --f6 '6543210.0'
    --i '456'
    --l 'foo'
    --s1 'a'
    --s2 'a b'
    --s3 '123e4'
    --s4 '-0.00034'
    --s5 ''
