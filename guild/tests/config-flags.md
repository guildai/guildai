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
            DEFAULT.b  (default is yes)
            DEFAULT.f  (default is 1.123)
            DEFAULT.i  (default is 123)
            DEFAULT.s  (default is 'hello there')
            foo.b      (default is 0)
            foo.f      (default is 2.234)
            foo.i      (default is 456)
            foo.s      (default is bye)
    <BLANKLINE>
        cfg-2
          Flags:
            f  (default is 2.234)
            i  (default is 456)
            s  (default is bye)
    <BLANKLINE>
        cfg-3
          Flags:
            DEFAULT.b  (default is yes)
            DEFAULT.f  (default is 1.123)
            DEFAULT.i  (default is 123)
            DEFAULT.s  (default is 'hello there')
            a.b.b      (default is 0)
            a.b.c.b    (default is no)
            a.b.c.f    (default is 3.321)
            a.b.c.i.1  (default is 789)
            a.b.c.i.2  (default is 12)
            a.b.c.s    (default is hi.again)
            a.b.i      (default is 456)
            a.b.s      (default is bye)
    <BLANKLINE>
        config-subdir-1
    <BLANKLINE>
        config-subdir-2
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
    <BLANKLINE>
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
            a.b.c    (default is 123)
            a.d      (default is 1.123)
            e.f      (default is hello)
            g.h      (default is 999)
            i.j.k.l  (default is 2)
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

### YAML v2

These tests in this section use `nested.yml`, which contains nested
values and uses dots in some keys.

Show the original config file.

    >>> cat("nested.yml")
    a:
      b:
        c: 123
      d: 1.123
    e:
      f: hello
    g.h: 999
    i.j:
      k.l: 2

Display results with default flags.

    >>> run("guild run yaml-nested -y")
    Resolving config:nested.yml
    {'a': {'b': {'c': 123}, 'd': 1.123},
     'e': {'f': 'hello'},
     'g.h': 999,
     'i.j': {'k.l': 2}}

Run with various modified flags.

    >>> run("guild run yaml-nested -y a.b.c=888 g.h=777")
    Resolving config:nested.yml
    {'a': {'b': {'c': 888}, 'd': 1.123},
     'e': {'f': 'hello'},
     'g.h': 777,
     'i.j': {'k.l': 2}}

    >>> run("guild run yaml-nested -y i.j.k.l=666 a.d=555")
    Resolving config:nested.yml
    {'a': {'b': {'c': 123}, 'd': 555},
     'e': {'f': 'hello'},
     'g.h': 999,
     'i.j': {'k.l': 666}}

Run with undefined flags using `--force-flags`.

    >>> run("guild run yaml-nested -y y=1 z.1=2 z.2=3 a.e=4 --force-flags")
    Resolving config:nested.yml
    {'a': {'b': {'c': 123}, 'd': 1.123, 'e': 4},
     'e': {'f': 'hello'},
     'g.h': 999,
     'i.j': {'k.l': 2},
     'y': 1,
     'z': {'1': 2, '2': 3}}

Run with an invalid flag.

    >>> run("guild run yaml-nested -y g.h.i=444 --force-flags")
    Resolving config:nested.yml
    guild: run failed because a dependency was not met: unexpected error resolving
    'config:nested.yml' in config:nested.yml resource: ValueError("'g.h.i' cannot
    be nested: conflicts with {'g.h': 999}")
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

    >>> run("guild run cfg -y")  # doctest: +REPORT_UDIFF
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

    >>> run("guild run cfg DEFAULT.b=no DEFAULT.i=321 foo.b=yes "
    ...     "foo.f=432.2 foo.s='hej hej' -y")
    ... # doctest: +REPORT_UDIFF
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

    >>> run("guild cat -p flags.cfg")  # doctest: +REPORT_UDIFF
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

    >>> run("guild run cfg-2 i=222 -y")  # doctest: +REPORT_UDIFF
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
    i = 222
    s = bye

Note that the flag assignment `i=222` results in `foo.i` being set to
`222`. This is by design according to the operation config, which maps
flags to alternative arg names (arg names being used in this case to
specify target section/options in the INI file).

### CFG v3

`cfg-3` uses `cfg-2.ini` to define flags, which uses dots in names
(dot-name keys).

Show the original INI file.

    >>> cat("flags-2.ini")
    [DEFAULT]
    # Values applied to sections below when not otherwise defined
    i = 123
    f = 1.123
    s = hello there
    b = yes
    <BLANKLINE>
    [a.b]
    i = 456
    s = bye
    b = 0
    <BLANKLINE>
    [a.b.c]
    i.1 = 789
    i.2 = 012
    f = 3.321
    s = hi.again
    b = False

Run `cfg-3` without specifying flag values.

    >>> run("guild run cfg-3 -y")  # doctest: +REPORT_UDIFF
    Resolving config:flags-2.ini
    [DEFAULT]
    b = True
    f = 1.123
    i = 123
    s = hello there
    <BLANKLINE>
    [a.b]
    b = 0
    i = 456
    s = bye
    <BLANKLINE>
    [a.b.c]
    b = False
    f = 3.321
    i.1 = 789
    i.2 = 12
    s = hi.again

Run the operation specifying various flag values.

    >>> run("guild run cfg-3 DEFAULT.i=222 DEFAULT.b=no a.b.i=333 "
    ...     "a.b.c.s='bye again' a.b.c.b=yes -y")
    ... # doctest: +REPORT_UDIFF
    Resolving config:flags-2.ini
    [DEFAULT]
    b = False
    f = 1.123
    i = 222
    s = hello there
    <BLANKLINE>
    [a.b]
    b = 0
    i = 333
    s = bye
    <BLANKLINE>
    [a.b.c]
    b = True
    f = 3.321
    i.1 = 789
    i.2 = 12
    s = bye again

Use `--force-flags` to insert values that aren't defined in the
original INI file.

    >>> run("guild run cfg-3 a.b.b=true a.b.new-attr=444 a.b.c.new-attr-2='hola' "
    ...     "--force-flags -y")
    ... # doctest: +REPORT_UDIFF
    Resolving config:flags-2.ini
    [DEFAULT]
    b = True
    f = 1.123
    i = 123
    s = hello there
    <BLANKLINE>
    [a.b]
    b = True
    i = 456
    new-attr = 444
    s = bye
    <BLANKLINE>
    [a.b.c]
    b = False
    f = 3.321
    i.1 = 789
    i.2 = 12
    new-attr-2 = hola
    s = hi.again

    >>> run("guild run cfg-3 DEFAULT.f=777.0 -y")
    ... # doctest: +REPORT_UDIFF
    Resolving config:flags-2.ini
    [DEFAULT]
    b = True
    f = 777.0
    i = 123
    s = hello there
    <BLANKLINE>
    [a.b]
    b = 0
    i = 456
    s = bye
    <BLANKLINE>
    [a.b.c]
    b = False
    f = 3.321
    i.1 = 789
    i.2 = 12
    s = hi.again

Apply new flag values to options containing dots.

    >>> run("guild run cfg-3 a.b.c.i.1=888 a.b.c.i.2=999 -y")
    ... # doctest: +REPORT_UDIFF
    Resolving config:flags-2.ini
    [DEFAULT]
    b = True
    f = 1.123
    i = 123
    s = hello there
    <BLANKLINE>
    [a.b]
    b = 0
    i = 456
    s = bye
    <BLANKLINE>
    [a.b.c]
    b = False
    f = 3.321
    i.1 = 888
    i.2 = 999
    s = hi.again

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

## Target paths

By default resolved `config` files are installed to the run directory
under the same subdirectories as their source relative to the Guild
file.

`config-subdir-1` specifies `config:subdir/flags.yml` as its flags
dest. The operation disabled source code copies so we can clear show
where the resolved config files are written under the run directory.

Show the config source.

    >>> cat("subdir/flags.yml")
    msg: hello

    >>> run("guild run config-subdir-1 -y")
    Resolving config:subdir/flags.yml

The resolved config file is located in the run directory under `subdir`.

    >>> run("guild ls -n")
    subdir/
    subdir/flags.yml

    >>> run("guild cat -p subdir/flags.yml")
    msg: hello

The target path can be configured by explicitly defining the config
resource. `config-subdir-2` shows how the same configuration file can
be written to the run directory root. It too disables source code
copies.

    >>> run("guild run config-subdir-2 -y")
    Resolving config:subdir/flags.yml

    >>> run("guild ls -n")
    flags.yml

    >>> run("guild cat -p flags.yml")
    msg: hello

## Restarting runs with param flags

When a run is restarted with flags destined for a config file, Guild
re-writes the config file with the new flag values.

We restart the last `json-in` operation.

    >>> last_run_id = run_capture("guild select -Fo json-in")

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

The project Guild file includes operation defined in
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
`flags.yml`. When resolved, `flags.yml` is written to `subdir` in the
run directory.

Show the original config file.

    >>> cat("subdir/flags.yml")
    msg: hello

Run `yaml-subdir-1`.

    >>> run("guild run yaml-subdir-1 -y")
    Resolving config:subdir/flags.yml

Show the resolved config file.

    >>> run("guild cat -p subdir/flags.yml")
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
