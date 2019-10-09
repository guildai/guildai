# Flag Values

These tests illustrate how Guild conveys flag values from both
configuration (Guild files) and user specified values on the command
line.

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
     'l': [1, 2, "a b 'c d'"],
     's1': 'a',
     's2': 'a b',
     's3': '123e4',
     's4': '-0.00034'}

Here's the output for the default values:

    >>> project.run("args")
    --b1 yes
    --b2 no
    --f1 1.1
    --f2 1.0
    --f3 0.1
    --f4 12300.0
    --f5 -6.78e-07
    --f6 6543210.0
    --i 456
    --l [1, 2, a b 'c d']
    --s1 a
    --s2 a b
    --s3 '123e4'
    --s4 '-0.00034'

We can change the values at the run command:

    >>> project.run("args", flags={
    ...   "b1": False,
    ...   "b2": True,
    ...   "s3": "hello",
    ...   "f4": "there",
    ... })
    --b1 no
    --b2 yes
    --f1 1.1
    --f2 1.0
    --f3 0.1
    --f4 there
    --f5 -6.78e-07
    --f6 6543210.0
    --i 456
    --l [1, 2, a b 'c d']
    --s1 a
    --s2 a b
    --s3 hello
    --s4 '-0.00034'

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
     'l': [1, 2, "a b 'c d'"],
     's1': 'a',
     's2': 'a b',
     's3': '123e4',
     's4': '-0.00034'}

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
    l: [1, 2, "a b 'c d'"]
    s1: 'a'
    s2: 'a b'
    s3: '123e4'
    s4: '-0.00034'

And with modified flags:

    >>> project.run("globals", flags={
    ...   "b1": False,
    ...   "b2": True,
    ...   "s3": "hello",
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
    l: [1, 2, "a b 'c d'"]
    s1: 'a'
    s2: 'a b'
    s3: 'hello'
    s4: '-0.00034'
