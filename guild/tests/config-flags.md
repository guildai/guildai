# Config Flags

Config flags are flags that are defined in config files.

Guild supports importing flag values from config files and dynamically
generating run-specific files using run flag values.

## Low Level Tests

    >>> from guild.plugins.config_flags import _iter_keyvals

    >>> def nested(data):
    ...     for name, val in sorted(_iter_keyvals(data)):
    ...         print("%s: %s" % (name, val))

    >>> nested({})

    >>> nested({"a": 123})
    a: 123

    >>> nested({"a": 123, "b": {"1": 456, "2": 789, "3": {"c": 876, "d": 543}}})
    a: 123
    b.1: 456
    b.2: 789
    b.3.c: 876
    b.3.d: 543

## Project Examples

We use the `config-flags` sample project for the tests below.

    >>> cd(sample("projects", "config-flags"))

For runs, we use a temp Guild home and a helper for running Guild
commands.

    >>> gh = mkdtemp()

    >>> def guild(cmd):
    ...     run("guild -H %s %s" % (gh, cmd))

Help for project contains imported flags.

    >>> guild("help")
    ???
    BASE OPERATIONS
    <BLANKLINE>
        cfg
          Flags:
            b      (default is yes)
            foo.b  (default is 0)
            foo.f  (default is 2.234)
            foo.i  (default is 456)
            foo.s  (default is bye)
            i      (default is 123)
    <BLANKLINE>
        json
          Flags:
            b    (default is yes)
            d.a  (default is A)
            d.b  (default is B)
            f    (default is 2.234)
            l    (default is 1 2 abc)
            s    (default is flu flam)
    <BLANKLINE>
        test-args-1
    <BLANKLINE>
        test-args-2
    <BLANKLINE>
        yaml
          Flags:
            b  (default is no)
            f  (default is 1.123)
            i  (default is 123)
            l  (default is 1 1.2 blue true)
            s  (default is Howdy Guild)
    <BLANKLINE>
        yaml-nested
          Flags:
            a.b.c  (default is 123)
            a.d    (default is 1.123)
            e.f    (default is hello)
    <BLANKLINE>
        yaml-subdir
          Flags:
            msg  (default is hello)
    <BLANKLINE>
        yaml-subdir-broken
    <exit 0>

## Supported File Types

### YAML

The original config file:

    >>> cat("flags.yml")
    i: 123
    f: 1.123
    s: Howdy Guild
    b: no
    l:
      - 1
      - 1.2
      - blue
      - yes
    d: {}
    <BLANKLINE>

Results with default flags:

    >>> guild("run yaml -y")
    Resolving config:flags.yml dependency
    {'b': False,
     'd': {},
     'f': 1.123,
     'i': 123,
     'l': '1 1.2 blue true',
     's': 'Howdy Guild'}
    <exit 0>

Results with modified flags:

    >>> guild("run yaml b=yes f=4.456 l='a b 123' s=hi -y")
    Resolving config:flags.yml dependency
    {'b': True, 'd': {}, 'f': 4.456, 'i': 123, 'l': 'a b 123', 's': 'hi'}
    <exit 0>

The config file is generated for the run.

    >>> guild("ls -n")
    flags.yml
    <exit 0>

    >>> guild("cat -p flags.yml")
    b: true
    d: {}
    f: 4.456
    i: 123
    l: a b 123
    s: hi
    <exit 0>

When Guild imports flags it assigns a type. An attempt to use an
invalid value generates an error.

    >>> guild("run yaml i=not-a-number -y")
    guild: invalid value not-a-number for i: invalid value for type 'number'
    <exit 1>

    >>> guild("run yaml f=not-a-number -y")
    guild: invalid value not-a-number for f: invalid value for type 'number'
    <exit 1>

### JSON

The original config file:

    >>> cat("flags.json")
    {
      "i": 456,
      "f": 2.234,
      "s": "flu flam",
      "b": true,
      "l": [1, 2, "abc"],
      "d": {
        "a": "A",
        "b": "B"
      }
    }

Results with default flags:

    >>> guild("run json -y")
    Resolving config:flags.json dependency
    {'b': True,
     'd': {'a': 'A', 'b': 'B'},
     'f': 2.234,
     'i': 456,
     'l': '1 2 abc',
     's': 'flu flam'}
    <exit 0>

Results with modified flags:

    >>> guild("run json s=abc -y")
    Resolving config:flags.json dependency
    {'b': True,
     'd': {'a': 'A', 'b': 'B'},
     'f': 2.234,
     'i': 456,
     'l': '1 2 abc',
     's': 'abc'}
    <exit 0>

Guild generates a run specific config file.

    >>> guild("ls -n")
    flags.json
    <exit 0>

    >>> guild("cat -p flags.json")
    {"b": true, "d": {"a": "A", "b": "B"}, "f": 2.234, "i": 456, "l": "1 2 abc", "s": "abc"}
    <exit 0>

### CFG

The original config file:

    >>> cat("flags.cfg")
    [DEFAULT]
    i = 123
    f = 1.123
    s = hello there
    b = yes
    <BLANKLINE>
    [foo]
    i = 456
    f = 2.234
    s = bye
    b = 0

When run with default values we get the same content. Note the order
of options is sorted.

    >>> guild("run cfg -y")
    Resolving config:flags.cfg dependency
    [DEFAULT]
    b = True
    f = 1.123
    i = 123
    s = hello there
    <BLANKLINE>
    [foo]
    b = 0
    f = 2.234
    i = 456
    s = bye
    <exit 0>

Run with modified flags.

    >>> guild("run cfg b=no i=321 foo.b=yes foo.f=432.2 foo.s='hej hej' -y")
    Resolving config:flags.cfg dependency
    [DEFAULT]
    b = False
    f = 1.123
    i = 321
    s = hello there
    <BLANKLINE>
    [foo]
    b = True
    f = 432.2
    i = 456
    s = hej hej
    <exit 0>

Guild generates a run specific config file.

    >>> guild("ls -n")
    flags.cfg
    <exit 0>

    >>> guild("cat -p flags.cfg")
    [DEFAULT]
    b = False
    f = 1.123
    i = 321
    s = hello there
    <BLANKLINE>
    [foo]
    b = True
    f = 432.2
    i = 456
    s = hej hej
    <exit 0>

## Implicit Dependency

## Defined Dependency

## Includes

Includes need to specify the path to the config file relative to the
importing source.

    >>> guild("run yaml-subdir -y")
    Resolving config:subdir/flags.yaml dependency
    <exit 0>

    >>> guild("ls -n")
    flags.yaml
    <exit 0>

If the path is relative to the imported source, Guild cannot find the
config file.

    >>> guild("run yaml-subdir-broken -y")
    <exit 0>

    >>> guild("ls -n")
    <BLANKLINE>
    <exit 0>

### Args Test

Guild passes only base args to the process command when `config`
destination is specified.

The `test-args-1` operation doesn't define any base args in
`guild.yml`.

    >>> guild("run test-args-1 -y")
    Resolving config:empty.json dependency
    []
    <exit 0>

The `test-args-2` operation defines three base args in `guild.yml`.

    >>> guild("run test-args-2 -y")
    Resolving config:empty.json dependency
    ['foo', 'bar', 'baz']
    <exit 0>
