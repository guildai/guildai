# Flag Values (op2)

TODO: append the section below to flag-vals.md and delete this front
matter -->

    >>> project = Project(sample("projects", "flag-vals"))
    >>> gf = guildfile.for_dir(project.cwd)

<--

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
     's4': '-0.00034'}

When we run this operation, it generates three trials:

    >>> with Env({"OP2": "1"}):
    ...     project.run("args-batch")
    INFO: [guild] Running trial ...: args-batch (b1=yes, b2=no, f1=1.1, f2=1.0,
    f3=0.1, f4=12300.0, f5=-6.78e-07, f6=6543210.0, i=456, l=1, s1=a, s2='a b',
    s3=1230000.0, s4='-0.00034')
    --b1 yes
    --b2 no
    --f1 1.1
    --f2 1.0
    --f3 0.1
    --f4 12300.0
    --f5 -6.78e-07
    --f6 6543210.0
    --i 456
    --l 1
    --s1 a
    --s2 a b
    --s3 1230000.0
    --s4 '-0.00034'
    INFO: [guild] Running trial ...: args-batch (b1=yes, b2=no, f1=1.1, f2=1.0,
    f3=0.1, f4=12300.0, f5=-6.78e-07, f6=6543210.0, i=456, l=2.3, s1=a, s2='a b',
    s3=1230000.0, s4='-0.00034')
    --b1 yes
    --b2 no
    --f1 1.1
    --f2 1.0
    --f3 0.1
    --f4 12300.0
    --f5 -6.78e-07
    --f6 6543210.0
    --i 456
    --l 2.3
    --s1 a
    --s2 a b
    --s3 1230000.0
    --s4 '-0.00034'
    INFO: [guild] Running trial ...: args-batch (b1=yes, b2=no, f1=1.1, f2=1.0,
    f3=0.1, f4=12300.0, f5=-6.78e-07, f6=6543210.0, i=456, l=foo, s1=a, s2='a b',
    s3=1230000.0, s4='-0.00034')
    --b1 yes
    --b2 no
    --f1 1.1
    --f2 1.0
    --f3 0.1
    --f4 12300.0
    --f5 -6.78e-07
    --f6 6543210.0
    --i 456
    --l foo
    --s1 a
    --s2 a b
    --s3 1230000.0
    --s4 '-0.00034'
