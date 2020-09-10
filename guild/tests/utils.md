# Guild utils

## Matching filters

    >>> from guild.util import match_filters

Empty case:

    >>> match_filters([], [])
    True

One filter for empty vals:

    >>> match_filters(["a"], [])
    False

No filters for vals:

    >>> match_filters([], ["a"])
    True

One filter matching one val:

    >>> match_filters(["a"], ["a"])
    True

One filter not matching one val:


    >>> match_filters(["a"], ["b"])
    False

One filter matching one of two vals:

    >>> match_filters(["a"], ["b", "a"])
    True

Two filters for empty vals:

    >>> match_filters(["a", "b"], [])
    False

Two filters for one matching where match_any is False (default):

    >>> match_filters(["a", "b"], ["a"])
    False

Two filters for one matching valwhere match_any is True:

    >>> match_filters(["a", "b"], ["a"], match_any=True)
    True

Two filters matching both vals:

    >>> match_filters(["a", "b"], ["a", "b"])
    True

Two filters matching both vals (alternate order);

    >>> match_filters(["a", "b"], ["b", "a"])
    True

## Resolving references

Use `resolve_refs` to resolve references in a string.

    >>> from guild.util import resolve_refs

Empty string:

    >>> resolve_refs("", {})
    ''

Missing ref generates an error:

    >>> resolve_refs("${a}", {})
    Traceback (most recent call last):
    UndefinedReferenceError: a

    >>> resolve_refs("foo ${bar} baz", {})
    Traceback (most recent call last):
    UndefinedReferenceError: bar

A default may be provided to use for missing values:

    >>> resolve_refs("${a}", {}, "")
    ''

    >>> resolve_refs("foo ${bar} baz", {}, "<missing>")
    'foo <missing> baz'

Single refs are resolved using the applicable typed value:

    >>> resolve_refs("${a}", {"a": "a"})
    'a'

    >>> resolve_refs("${a}", {"a": 123})
    123

    >>> resolve_refs("${a}", {"a": 1.234})
    1.234

    >>> resolve_refs("${a}", {"a": True})
    True

    >>> print(resolve_refs("${a}", {"a": None}))
    None

    >>> print(resolve_refs("${a}", {"a": [1, 'a', True, None]}))
    [1, 'a', True, None]

When used in a string, resolved refs are encoded:

    >>> resolve_refs("foo ${bar} baz", {"bar": "bar"})
    'foo bar baz'

    >>> resolve_refs("foo ${bar} baz", {"bar": 123})
    'foo 123 baz'

    >>> resolve_refs("foo ${bar} baz", {"bar": 1.234})
    'foo 1.234 baz'

    >>> resolve_refs("foo ${bar} baz", {"bar": True})
    'foo true baz'

    >>> resolve_refs("foo ${bar} baz", {"bar": None})
    'foo null baz'

    >>> normlf(resolve_refs(
    ...     "foo ${bar} baz",
    ...     {"bar": [1, 'a', True, None]})) # doctest: -NORMALIZE_PATHS
    'foo - 1\n- a\n- true\n- null baz'

Escaped references aren't resolved:

    >>> resolve_refs("\${a}", {}) # doctest: -NORMALIZE_PATHS
    '${a}'

    >>> resolve_refs("\${a}", {"a": "a"}) # doctest: -NORMALIZE_PATHS
    '${a}'

    >>> resolve_refs("foo \${bar} baz", {}) # doctest: -NORMALIZE_PATHS
    'foo ${bar} baz'

    >>> resolve_refs("foo \${bar} baz", {"bar": "bar"}) # doctest: -NORMALIZE_PATHS
    'foo ${bar} baz'

### `resolve_all_refs`

A map of vals may contain references to other vals. Use
`resolve_all_refs` to resolve all references in the map.

    >>> from guild.util import resolve_all_refs

No references:

    >>> resolve_all_refs({"a": 1})
    {'a': 1}

    >>> resolve_all_refs({"a": "1"})
    {'a': '1'}

Reference to undefined value:

    >>> resolve_all_refs({"a": "${b}"})
    Traceback (most recent call last):
    UndefinedReferenceError: b

    >>> resolve_all_refs({"a": "${b}"}, undefined="foo")
    {'a': 'foo'}

Reference to a value:

    >>> pprint(resolve_all_refs({"a": "${b}", "b": 1}))
    {'a': 1, 'b': 1}

Reference to a value with a reference:

    >>> pprint(resolve_all_refs({"a": "${b}", "b": "${c}", "c": 1}))
    {'a': 1, 'b': 1, 'c': 1}

Reference embedded in a string:

    >>> pprint(resolve_all_refs({"a": "b equals ${b}", "b": 1}))
    {'a': 'b equals 1', 'b': 1}

    >>> resolve_all_refs(
    ... {"msg": "${x} + ${y} = ${z}",
    ...  "x": "one",
    ...  "y": "two",
    ...  "z": "three"})["msg"]
    'one + two = three'

Reference cycle:

    >>> resolve_all_refs({"a": "${b}", "b": "${a}"})
    Traceback (most recent call last):
    ReferenceCycleError: ['b', 'a', 'b']

Resolving non string values:

    >>> resolve_all_refs({
    ...   "msg": "${i} ${f} ${none}",
    ...   "i": 1,
    ...   "f": 1.2345,
    ...   "none": None})["msg"]
    '1 1.2345 null'

Note that None is resolved as 'null' for consistency with flag inputs,
which convert the string 'null' into None.

A reference can be escaped:

    >>> resolve_all_refs({"a": "\${foo}"})
    {'a': '${foo}'}

## Testing text files

Use `is_text_file` to test if a file is text or binary. This is used
to provide a file viewer for text files.

    >>> from guild.util import is_text_file

The test uses known file extensions as an optimization. To test the
file content itself, we need to ignore extensions:

    >>> def is_text(sample_path):
    ...     path = sample("textorbinary", sample_path)
    ...     return is_text_file(path, ignore_ext=True)

Our samples:

    >>> is_text("cookiecutter.json")
    True

    >>> is_text("empty.pyc")
    False

    >>> is_text("empty.txt")
    True

    >>> is_text("hello.py")
    True

    >>> is_text("hello_world.pyc")
    False

    >>> is_text("lena.gif")
    False

    >>> is_text("lena.jpg")
    False

    >>> is_text("lookup-error")
    False

    >>> is_text("lookup-error.txt")
    True

A non-existing file generates an error:

    >>> is_text("non-existing")
    Traceback (most recent call last):
    OSError: .../samples/textorbinary/non-existing does not exist

Directories aren't text files:

    >>> is_text(".")
    False

## Run output

Run output can be read using util.RunOutputReader.

    >>> from guild.util import RunOutputReader

For these tests, we'll use a sample run:

    >>> run_dir = sample("runs/7d145216ae874020b735f001a7bfd27d")

Our reader:

    >>> reader = RunOutputReader(run_dir)

We use the `read` method to read output. By default `read` returns all
available output.

    >>> reader.read()
    [(1524584359781, 0, 'Tue Apr 24 10:39:19 CDT 2018'),
     (1524584364782, 0, 'Tue Apr 24 10:39:24 CDT 2018'),
     (1524584369785, 0, 'Tue Apr 24 10:39:29 CDT 2018'),
     (1524584374790, 0, 'Tue Apr 24 10:39:34 CDT 2018')]

We can alternatively read using start and end indices.

    >>> reader.read(0, 0)
    [(1524584359781, 0, 'Tue Apr 24 10:39:19 CDT 2018')]

    >>> reader.read(1, 1)
    [(1524584364782, 0, 'Tue Apr 24 10:39:24 CDT 2018')]

    >>> reader.read(2, 3)
    [(1524584369785, 0, 'Tue Apr 24 10:39:29 CDT 2018'),
     (1524584374790, 0, 'Tue Apr 24 10:39:34 CDT 2018')]

If start is omitted, output is read form the start.

    >>> reader.read(end=2)
    [(1524584359781, 0, 'Tue Apr 24 10:39:19 CDT 2018'),
     (1524584364782, 0, 'Tue Apr 24 10:39:24 CDT 2018'),
     (1524584369785, 0, 'Tue Apr 24 10:39:29 CDT 2018')]

If end is omitted, output is read to the end.

    >>> reader.read(start=2)
    [(1524584369785, 0, 'Tue Apr 24 10:39:29 CDT 2018'),
     (1524584374790, 0, 'Tue Apr 24 10:39:34 CDT 2018')]

When we're run reading we can close the reader:

    >>> reader.close()

## Safe rmtree check

The function `safe_rmtree` will fail if the specified path is a
top-level directory. Top level is defined as either the root or a
directory in the root.

The function `_top_level_dir` is used for this test.

    >>> from guild.util import _top_level_dir

Tests:

    >>> import os

    >>> _top_level_dir(os.path.sep)
    True

    >>> _top_level_dir(os.path.join(os.path.sep, "foo"))
    True

    >>> _top_level_dir(os.path.join(os.path.sep, "foo", "bar"))
    False

    >>> _top_level_dir(".")
    False

## Shlex quote

    >>> from guild.util import shlex_quote as quote

    >>> quote(None)
    "''"

    >>> quote("")
    "''"

    >>> quote("foo")
    'foo'

    >>> quote("foo bar")
    "'foo bar'"

    >>> quote("/foo/bar")
    '/foo/bar'

    >>> quote("/foo bar")
    "'/foo bar'"

    >>> quote("\\foo\\bar")  # doctest: -NORMALIZE_PATHS
    "'\\foo\\bar'"

    >>> quote("D:\\foo\\bar")  # doctest: -NORMALIZE_PATHS
    "'D:\\foo\\bar'"

    >>> quote("D:\\foo bar")  # doctest: -NORMALIZE_PATHS
    "'D:\\foo bar'"

    >>> quote("'a b c'")  # doctest: -NORMALIZE_PATHS
    '"\'a b c\'"'

    >>> quote("~")
    "'~'"

    >>> quote("a ~ b")
    "'a ~ b'"

    >>> quote("*")
    "'*'"

    >>> quote("?")
    "'?'"

## Shlex split

    >>> from guild.util import shlex_split as split

    >>> split(None)
    []

    >>> split("")
    []

    >>> split("foo")
    ['foo']

    >>> split("foo bar")
    ['foo', 'bar']

    >>> split("'foo bar'")
    ['foo bar']

    >>> split("'foo bar' baz")
    ['foo bar', 'baz']

    >>> split("'/foo/bar'")
    ['/foo/bar']

    >>> split("'/foo bar'")
    ['/foo bar']

    >>> split("'/foo bar' baz bam")
    ['/foo bar', 'baz', 'bam']

    >>> split("'\\foo\\bar'") # doctest: -NORMALIZE_PATHS
    ['\\foo\\bar']

## Nested config

    >>> from guild.util import nested_config as nc

    >>> nc({})
    {}

    >>> nc({"1": 1})
    {'1': 1}

    >>> nc({"1.1": 11})
    {'1': {'1': 11}}

    >>> pprint(nc({"1.1": 11, "1.2": 12}))
    {'1': {'1': 11, '2': 12}}

Cannot nest within a non-dict:

    >>> pprint(nc({"1": 1, "1.1": 11, "1.2": 12}))
    Traceback (most recent call last):
    ValueError: '1.1' cannot be nested: conflicts with {'1': 1}

    >>> pprint(nc({"1.2": 12, "1.1.1": 111, "1.2.1": 121}))
    Traceback (most recent call last):
    ValueError: '1.2.1' cannot be nested: conflicts with {'1.2': 12}

An explicit dict is okay:

    >>> pprint(nc({"1.2": {}, "1.1.1": 111, "1.2.1": 121}))
    {'1': {'1': {'1': 111}, '2': {'1': 121}}}

## Shorten dirs

The function `util.shorten_path()` is used to shorten directories by
removing path segments and replacing them with an ellipsis ('...') as
needed to keep them under a specified length.

    >>> from guild.util import shorten_path
    >>> shorten = lambda s, max_len: shorten_path(s, max_len, sep="/")

Any paths under the specified length are returned unmodified:

    >>> shorten("/foo/bar/baz", max_len=20)
    '/foo/bar/baz'

If a path is longer than `max_len`, the function tries to shorten it
by replacing path segments with an ellipsis.

If a path has fewer then two segments, it is returned unmodified
regardless of the max length:

    >>> shorten("foo", max_len=0)
    'foo'

If a shortened path is not actually shorter than the original path,
the original path is returned unmodified.

    >>> shorten("/a/b", max_len=0)
    '/a/b'

    >>> shorten("/aaa/bbb/ccc", max_len=12)
    '/aaa/bbb/ccc'

The function attempts to include as much of the original path in the
shortened version as possible. It will always at least include the
last segment in a shortened version.

    >>> shorten("/aaa/bbb/ccc", max_len=0) # doctest: -ELLIPSIS
    '/\u2026/ccc'

If able to, the function includes path segments from both the left and
right sides.

    >>> shorten("/aaa/bbbb/ccc", max_len=12) # doctest: -ELLIPSIS
    '/aaa/\u2026/ccc'

The function checks each segment side, starting with the right side
and then alternating, to include segment parts. It stops when the
shortened path would exceed max length.

    >>> shorten("/aaa/bbbb/cccc/ddd", max_len=17) # doctest: -ELLIPSIS
    '/aaa/\u2026/cccc/ddd'

    >>> shorten("/aaa/bbbb/cccc/ddd", max_len=16) # doctest: -ELLIPSIS
    '/aaa/\u2026/cccc/ddd'

    >>> shorten("/aaa/bbbb/cccc/ddd", max_len=12) # doctest: -ELLIPSIS
    '/aaa/\u2026/ddd'

    >>> shorten("/aaa/bbbb/cccc/ddd", max_len=0) # doctest: -ELLIPSIS
    '/\u2026/ddd'

The same rules applied to relative paths:

    >>> shorten("aaa/bbbb/cccc/ddd", max_len=16) # doctest: -ELLIPSIS
    'aaa/\u2026/cccc/ddd'

    >>> shorten("aaa/bbbb/cccc/ddd", max_len=15) # doctest: -ELLIPSIS
    'aaa/\u2026/cccc/ddd'

    >>> shorten("aaa/bbbb/cccc/ddd", max_len=11) # doctest: -ELLIPSIS
    'aaa/\u2026/ddd'

    >>> shorten("aaa/bbbb/cccc/ddd", max_len=0) # doctest: -ELLIPSIS
    'aaa/\u2026/ddd'

### Splitting paths for shorten dir

The shorten dir algorithm uses `util._shorten_path_split_path`, which
handles cases of leading and repeating path separators by appending
them to the next respective part.

    >>> from guild.util import _shorten_path_split_path
    >>> ds_split = lambda s: _shorten_path_split_path(s, "/")

Examples:

    >>> ds_split("")
    []

    >>> ds_split("/")
    ['/']

    >>> ds_split("foo")
    ['foo']

    >>> ds_split("/foo")
    ['/foo']

    >>> ds_split("foo/bar")
    ['foo', 'bar']

    >>> ds_split("/foo/bar")
    ['/foo', 'bar']

    >>> ds_split("/foo/bar/")
    ['/foo', 'bar']

    >>> ds_split("//foo//bar")
    ['//foo', '/bar']

## Removing item from lists

The functions `safe_list_remove` and `safe_list_remove_all` are used
to safely remove items from lists.

    >>> from guild.util import safe_list_remove
    >>> from guild.util import safe_list_remove_all

Helper functions:

    >>> def rm(x, l):
    ...     safe_list_remove(x, l)
    ...     pprint(l)

    >>> def rm_all(xs, l):
    ...     safe_list_remove_all(xs, l)
    ...     pprint(l)

Examples:

    >>> rm(1, [1])
    []

    >>> rm(1, [])
    []

    >>> rm(1, [2])
    [2]

    >>> rm_all([1, 2], [2, 1])
    []

    >>> rm_all([1, 2], [])
    []

    >>> rm_all([1, 2], [2, 3])
    [3]

## Testing subdirectories

    >>> from guild.util import subpath

    >>> subpath("/foo/bar", "/foo", "/")
    'bar'

    >>> subpath("/foo/bar", "/bar", "/")
    Traceback (most recent call last):
    ValueError: ('/foo/bar', '/bar')

    >>> subpath("/foo", "/foo", "/")
    Traceback (most recent call last):
    ValueError: ('/foo', '/foo')

    >>> subpath("/foo/", "/foo", "/")
    ''

    >>> subpath("", "", "/")
    Traceback (most recent call last):
    ValueError: ('', '')

    >>> subpath("/", "/", "/")
    Traceback (most recent call last):
    ValueError: ('/', '/')

## YAML support

### Encode

    >>> from guild.util import encode_yaml

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

### Decode

    >>> from guild.util import decode_yaml

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

## File names

When writing files the `safe_filename` function is used to ensure the
file name is valid for a platform.

    >>> from guild.util import safe_filename

On Windows, the function replaces colons with underscores.

    >>> safe_filename("hello:there")  # doctest: +WINDOWS_ONLY
    'hello_there'

On all platforms, the function replaces any possible path separator
with underscore.

    >>> safe_filename("hello/there\\friend")
    'hello_there_friend'
