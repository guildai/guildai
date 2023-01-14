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

    >>> use_project("config-flags")

    >>> run("guild help")  # doctest: +REPORT_UDIFF
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
        cfg-2
          Flags:
            f  (default is 2.234)
            i  (default is 456)
            s  (default is bye)
    <BLANKLINE>
       explicit-no-replace
         Flags:
           b    (default is yes)
           d.a  (default is A)
           d.b  (default is B)
           f    (default is 2.234)
           i    (default is 456)
           l    (default is '1 2 abc')
           s    (default is 'flu flam')
    <BLANKLINE>
        json
          Flags:
            b    (default is yes)
            d.a  (default is A)
            d.b  (default is B)
            f    (default is 2.234)
            l    (default is '1 2 abc')
            s    (default is 'flu flam')
    <BLANKLINE>
        json-2
          Flags:
            aa  (default is A)
            bb  (default is BB)
        json-in
          Flags:
            b    (default is yes)
            d.a  (default is A)
            d.b  (default is B)
            f    (default is 2.234)
            i    (default is 456)
            l    (default is '1 2 abc')
            s    (default is 'flu flam')
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
            l  (default is '1 1.2 blue true')
            s  (default is 'Howdy Guild')
    <BLANKLINE>
        yaml-nested
          Flags:
            a.b.c  (default is 123)
            a.d    (default is 1.123)
            e.f    (default is hello)
    <BLANKLINE>
        yaml-subdir-1
          Flags:
            msg  (default is hello)
    <BLANKLINE>
        yaml-subdir-2
          Flags:
            b  (default is no)
            f  (default is 1.123)
            i  (default is 123)
            l  (default is '1 1.2 blue true')
            s  (default is 'Howdy Guild')

## Supported File Types

Guild supports various config file formats, which are tested below.

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

Results with default flags:

    >>> run("guild run yaml -y")
    Resolving config:flags.yml
    {'b': False,
     'd': {},
     'f': 1.123,
     'i': 123,
     'l': [1, 1.2, 'blue', True],
     's': 'Howdy Guild'}

Results with modified flags:

    >>> run("guild run yaml b=yes f=4.456 l='a b 123' s=hi -y")
    Resolving config:flags.yml
    {'b': True, 'd': {}, 'f': 4.456, 'i': 123, 'l': ['a', 'b', 123], 's': 'hi'}

The config file generated for the run contains the user-specified flag
values.

    >>> run("guild cat -p flags.yml")
    b: true
    d: {}
    f: 4.456
    i: 123
    l:
    - a
    - b
    - 123
    s: hi

When Guild imports flags it assigns a type. An attempt to use an
invalid value generates an error.

    >>> run("guild run yaml i=not-a-number -y")
    guild: invalid value not-a-number for i: invalid value for type 'number'
    <exit 1>

    >>> run("guild run yaml f=not-a-number -y")
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

    >>> run("guild run json -y")
    Resolving config:flags.json
    {'b': True,
     'd': {'a': 'A', 'b': 'B'},
     'f': 2.234,
     'i': 456,
     'l': [1, 2, 'abc'],
     's': 'flu flam'}

Results with modified flags:

    >>> run("guild run json s=abc l=\"2 1 'a b' d\" -y")
    Resolving config:flags.json
    {'b': True,
     'd': {'a': 'A', 'b': 'B'},
     'f': 2.234,
     'i': 456,
     'l': [2, 1, 'a b', 'd'],
     's': 'abc'}

Guild generates a run specific config file.

    >>> run("guild cat -p flags.json")
    {"b": true, "d": {"a": "A", "b": "B"}, "f": 2.234,
    "i": 456, "l": [2, 1, "a b", "d"], "s": "abc"}

### JSON v2

The `json-2` operation maps flags names to different locations in the
JSON file.

    >>> run("guild run json-2 -y")
    Resolving config:flags.json
    {'b': True,
     'd': {'a': 'A', 'b': 'BB'},
     'f': 2.234,
     'i': 456,
     'l': [1, 2, 'abc'],
     's': 'flu flam'}

    >>> run("guild run json-2 aa=AAA bb=B -y")
    Resolving config:flags.json
    {'b': True,
     'd': {'a': 'AAA', 'b': 'B'},
     'f': 2.234,
     'i': 456,
     'l': [1, 2, 'abc'],
     's': 'flu flam'}

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

    >>> run("guild run cfg -y")
    Resolving config:flags.cfg
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

Run with modified flags.

    >>> run("guild run cfg b=no i=321 foo.b=yes foo.f=432.2 foo.s='hej hej' -y")
    Resolving config:flags.cfg
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

Guild generates a run specific config file.

    >>> run("guild cat -p flags.cfg")
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

### CFG v2

The `cfg-2` operation maps alternative flag names to various INI
entries.

    >>> run("guild run cfg-2 i=222 -y")
    Resolving config:flags.cfg
    [DEFAULT]
    b = yes
    f = 1.123
    i = 123
    s = hello there
    <BLANKLINE>
    [foo]
    b = 0
    f = 2.234
    i = 222
    s = bye

### `.in` files

Guild supports all of the above extensions when named with a `.in`
extension.

We use the `json-in` operation as an example.

The json input 'flags.json.in':

    >>> cat("flags.json.in")
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

    >>> run("guild run json-in -y")
    Resolving config:flags.json.in
    {'b': True,
     'd': {'a': 'A', 'b': 'B'},
     'f': 2.234,
     'i': 456,
     'l': [1, 2, 'abc'],
     's': 'flu flam'}

Results with modified flags:

    >>> run("guild run json-in s=abc l=\"2 1 'a b' d\" -y")
    Resolving config:flags.json.in
    {'b': True,
     'd': {'a': 'A', 'b': 'B'},
     'f': 2.234,
     'i': 456,
     'l': [2, 1, 'a b', 'd'],
     's': 'abc'}

Guild generates a run specific config file.

    >>> run("guild cat -p flags.json")
    {"b": true, "d": {"a": "A", "b": "B"}, "f": 2.234, "i": 456,
    "l": [2, 1, "a b", "d"], "s": "abc"}

## Restarting runs with param flags

When a run is restarted with flags destined for a config file, Guild
re-writes the config file with the new flag values.

    >>> last_run_id = run_capture("guild select")

    >>> run(f"guild run --restart {last_run_id} b=no f=3.345 -y")
    Resolving config:flags.json.in
    {'b': False,
     'd': {'a': 'A', 'b': 'B'},
     'f': 3.345,
     'i': 456,
     'l': [2, 1, 'a b', 'd'],
     's': 'abc'}

If an operation explicitly defines a config resource to not re-resolve
on restart, Guild fails on restart. We use the `explicit-no-replace`
operation to test this.

Generate a run to restart:

    >>> run("guild run explicit-no-replace -y")
    Resolving config:flags.json

Restart the run:

    >>> last_run_id = run_capture("guild select")

    >>> run(f"guild run --restart {last_run_id} -y")
    Resolving config:flags.json
    Skipping resolution of config:flags.json because it's already resolved
    <exit 0>

## Handling unsupported config file extensions

To illustrate how Guild handles unsupported file extensions, we create
a new project.

    >>> use_project(mkdtemp())
    >>> write("guild.yml", """
    ... invalid-config:
    ...   main: guild.pass
    ...   flags-dest: config:params.badext
    ...   flags-import: all
    ... """)

    >>> run("guild ops")
    WARNING: config type for params.badext not supported
    invalid-config

## Includes

Includes need to specify the path to the config file relative to the
importing source.

We return to the `config-flags` sample project to illustate.

    >>> use_project("config-flags")

The project Guild file includes operation defines in
`subdir/guild-config.yml`.

    >>> cat("guild.yml")
    - include: subdir/guild-config.yml
    <BLANKLINE>
    - operations:
        $include: subdir-ops
    ...

    >>> cat(path("subdir", "guild-config.yml"))  # doctest: +REPORT_UDIFF
    - config: subdir-ops
      operations:
        yaml-subdir-1:
          main: guild.pass
          flags-dest: config:subdir/flags.yml
          flags-import: yes
    <BLANKLINE>
        yaml-subdir-2:
          main: guild.pass
          flags-dest: config:flags.yml
          flags-import: yes

The `yaml-subdir-1` operation includes `subdir` as a parent of
`flags.yml`.

    >>> run("guild run yaml-subdir-1 -y")
    Resolving config:subdir/flags.yml

The resolved config file originated from `subdir`.

    >>> run("guild cat -p flags.yml")
    msg: hello

`yaml-subdir-2` does not include `subdir`. When it's resolved, it's
resolved relative to the importing source.

    >>> run("guild run yaml-subdir-2 -y")
    Resolving config:flags.yml

    >>> run("guild cat -p flags.yml")
    b: false
    d: {}
    f: 1.123
    i: 123
    l:
    - 1
    - 1.2
    - blue
    - true
    s: Howdy Guild

### Args Test

Guild passes only base args to the process command when `config`
destination is specified.

The `test-args-1` operation doesn't define any base args in
`guild.yml`.

    >>> gf_data = yaml.safe_load(open("guild.yml"))
    >>> pprint(gf_data[1]["operations"]["test-args-1"])
    {'flags-dest': 'config:empty.json',
     'flags-import': 'all',
     'main': 'test_args'}

The operatioin prints `sys.argv[1:]`.

    >>> run("guild run test-args-1 -y")
    Resolving config:empty.json
    []

`test-args-2` operation defines three base args in `guild.yml`.

    >>> pprint(gf_data[1]["operations"]["test-args-2"])
    {'flags-dest': 'config:empty.json',
     'flags-import': 'all',
     'main': 'test_args foo bar baz'}
