# YAML Utils

## Encode

    >>> from guild.yaml_util import encode_yaml

    >>> encode_yaml(1)
    '1'

    >>> encode_yaml(1.123)
    '1.123'

    >>> encode_yaml("a")
    'a'

    >>> encode_yaml("1")
    "'1'"

    >>> encode_yaml("1.123")
    "'1.123'"

    >>> encode_yaml("1e2")
    "'1e2'"

    >>> encode_yaml("1.0e2")
    "'1.0e2'"

    >>> encode_yaml("1.0e-2")
    "'1.0e-2'"

    >>> encode_yaml("+1.0e+2")
    "'+1.0e+2'"

    >>> encode_yaml(True)
    'true'

    >>> encode_yaml(False)
    'false'

    >>> import datetime
    >>> encode_yaml(datetime.datetime(2010, 1, 1))
    '2010-01-01 00:00:00'

    >>> normlf(encode_yaml([1, "a", 1e2, datetime.datetime(2010, 5, 15),
    ...                     True, False]))  # doctest: -NORMALIZE_PATHS
    '- 1\n- a\n- 100.0\n- 2010-05-15 00:00:00\n- true\n- false'

## Decode

    >>> from guild.yaml_util import decode_yaml

    >>> decode_yaml("1")
    1

    >>> decode_yaml("1.123")
    1.123

    >>> decode_yaml("1e2")
    100.0

    >>> decode_yaml("1.0e2")
    100.0

    >>> decode_yaml("1.0e-2")
    0.01

    >>> decode_yaml("+1.0e+2")
    100.0

    >>> decode_yaml("a")
    'a'

    >>> decode_yaml("'1e2'")
    '1e2'

    >>> decode_yaml("'1.0e2'")
    '1.0e2'

    >>> decode_yaml("'1.0e-2'")
    '1.0e-2'

    >>> decode_yaml("'+1.0e+2'")
    '+1.0e+2'

    >>> decode_yaml("true")
    True

    >>> decode_yaml("TRUE")
    True

    >>> decode_yaml("false")
    False

    >>> decode_yaml("yes")
    True

    >>> decode_yaml("no")
    False

    >>> decode_yaml("No")
    False

    >>> decode_yaml("on")
    True

    >>> decode_yaml("off")
    False

    >>> decode_yaml("OFF")
    False

    >>> import datetime
    >>> decode_yaml("2010-01-01 00:00:00")
    datetime.datetime(2010, 1, 1, 0, 0)

    >>> pprint(decode_yaml("foo: 123\nbar: 456"))
    {'bar': 456, 'foo': 123}

    >>> decode_yaml("[1, b, yes, 1e2, 2010-05-15]")
    [1, 'b', True, 100.0, datetime.date(2010, 5, 15)]

PyYAML deviates from the [YAML
standard](https://yaml.org/type/bool.html) when reading single
character variants of booleans.

    >>> decode_yaml("y")
    'y'

    >>> decode_yaml("n")
    'n'

    >>> decode_yaml("Y")
    'Y'

    >>> decode_yaml("N")
    'N'

From Guild's standpoint, this behavior is desirable as it allows users
to naturally express single char keys without requiring that they
quote them.

    >>> pprint(decode_yaml("""
    ... flags:
    ...   x: 123
    ...   y: 456
    ... """))
    {'flags': {'x': 123, 'y': 456}}

The strict implementation of the YAML standard would require users to
quote 'y'.

    >>> pprint(decode_yaml("""
    ... flags:
    ...   x: 123
    ...   'y': 456
    ... """))
    {'flags': {'x': 123, 'y': 456}}

However, when PyYAML encodes single character booleans without quoting
them, it generates invalid YAML that cannot be correctly read by other
parsers. See *Guild modified behavior* below for how Guild addresses
this.

## YAML Front Matter

    >>> from guild.yaml_util import yaml_front_matter as yfm

    >>> tmp = mkdtemp()
    >>> working = path(tmp, "working")

    >>> write(working, "")
    >>> yfm(working)
    {}

    >>> write(working, """---
    ... ---
    ... """)
    >>> yfm(working)
    {}

    >>> write(working, """---
    ... i: 123
    ... f: 1.123
    ... s: hello
    ... ---
    ...
    ... Some non-front matter content.
    ... """)
    >>> pprint(yfm(working))
    {'f': 1.123, 'i': 123, 's': 'hello'}

    >>> write(working, """---
    ... - foo
    ... - bar
    ... - baz: 123
    ...   bam: 456
    ... ---
    ...
    ... Some non-front matter content.
    ... """)
    >>> pprint(yfm(working))
    ['foo', 'bar', {'bam': 456, 'baz': 123}]

## Guild modified behavior

Guild patches the `yaml` package to facilitate some of the above
encoding/decoding features.

- Supports a more flexible scheme for specifying floats
- Encoders single character variants of boolean as strings

Function to decode a string using the unpatched PyYAML library:

    >>> def decode_yaml_unpatched(s):
    ...    out = run_capture("python -c \""
    ...        "import yaml, json; "
    ...        f"decoded = yaml.safe_load('{s}'); "
    ...        "print(json.dumps(decoded))"
    ...        "\"")
    ...    return json.loads(out)

### Decoding floats

PyYAML requires both an explicit sign ('+' or '-') and a decimal to
decode floats.

Missing a sign:

    >>> decode_yaml_unpatched("1.0e2")
    '1.0e2'

Missing a decimal:

    >>> decode_yaml_unpatched("+1e2")
    '+1e2'

    >>> decode_yaml_unpatched("-1e2")
    '-1e2'

Missing both a sign and a decimal:

    >>> decode_yaml_unpatched("1e2")
    '1e2'

Guild's patched `yaml` decodes all cases as float.

    >>> decode_yaml("1.0e2")
    100.0

    >>> decode_yaml("+1e2")
    100.0

    >>> decode_yaml("-1e2")
    -100.0

    >>> decode_yaml("1e2")
    100.0

### Encoding single char booleans

PyYAML writes single char booleans ('y', 'n', 'Y', and 'N") without
quotes. While PyYAML decodes these as single chars, parsers that
comply with the YAML standard for booleans will decode these as
booleans. Without quoting, Guild-saved YAML values that contain these
chars are invalid for YAML-compliant parsers.

    >>> encode_yaml("y")
    'y'

    >>> encode_yaml("n")
    'n'

    >>> encode_yaml("Y")
    'Y'

    >>> encode_yaml("N")
    'N'

Patched, single char boolean chars are quoted.

    >>> from guild.yaml_util import StrictPatch
    >>> patch = StrictPatch()

    >>> with patch:
    ...     encode_yaml("y")
    "'y'"

    >>> with patch:
    ...     encode_yaml("n")
    "'n'"

    >>> with patch:
    ...     encode_yaml("Y")
    "'Y'"

    >>> with patch:
    ...     encode_yaml("N")
    "'N'"

Similarly, single char boolean chars are decoded as booleans.

    >>> with patch:
    ...     decode_yaml("y")
    True

    >>> with patch:
    ...     decode_yaml("n")
    False

    >>> with patch:
    ...     decode_yaml("Y")
    True

    >>> with patch:
    ...     decode_yaml("N")
    False

Non-boolean single chars are not quoted.

    >>> with patch:
    ...     encode_yaml("a")
    'a'

Patching does not have an effect outside the patch context.

    >>> encode_yaml("y")
    'y'

    >>> encode_yaml("n")
    'n'

    >>> encode_yaml("Y")
    'Y'

    >>> encode_yaml("N")
    'N'

    >>> decode_yaml("y")
    'y'

    >>> decode_yaml("n")
    'n'

    >>> decode_yaml("Y")
    'Y'

    >>> decode_yaml("N")
    'N'
