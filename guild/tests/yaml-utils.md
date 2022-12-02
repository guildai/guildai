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

    >>> decode_yaml("false")
    False

    >>> decode_yaml("yes")
    True

    >>> decode_yaml("no")
    False

    >>> decode_yaml("on")
    True

    >>> decode_yaml("off")
    False

    >>> import datetime
    >>> decode_yaml("2010-01-01 00:00:00")
    datetime.datetime(2010, 1, 1, 0, 0)

    >>> pprint(decode_yaml("foo: 123\nbar: 456"))
    {'bar': 456, 'foo': 123}

    >>> decode_yaml("[1, b, yes, 1e2, 2010-05-15]")
    [1, 'b', True, 100.0, datetime.date(2010, 5, 15)]

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

## Decoding 'y/Y' and 'n/N'

The [YAML spec for bool](https://yaml.org/type/bool.html) includes
single char alternative spellings for true and false: 'y/Y' and 'n/N'
respectively.

The `PyYAML` library [does not support
these](https://github.com/yaml/pyyaml/issues/247) and so we patch the
library.

    >>> decode_yaml("y")
    True

    >>> decode_yaml("n")
    False

    >>> decode_yaml("Y")
    True

    >>> decode_yaml("N")
    False
