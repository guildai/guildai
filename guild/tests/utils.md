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

Nested config is encoded using a flat mapping of dot-delimited names
to values. When decoded, nested config is represented by a deep dict
using dots to denote levels in the decoded dict.

### Decoding nested config

The decoding function is `guild.util.nested_config`. It takes a flag
map of dot-delimeted names to values.

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

### Encoding nested config

The function `guild.util.encode_nested_config` is used to encode a
deep dict to a flat dict with dot-delimited names.

    >>> from guild.util import encode_nested_config as enc

    >>> enc({})
    {}

    >>> enc({"a": "A"})
    {'a': 'A'}

    >>> pprint(enc({"a.a1": "A1", "a.a2": "A2"}))
    {'a.a1': 'A1', 'a.a2': 'A2'}

    >>> enc({"1": {"1": 11}})
    {'1.1': 11}

    >>> pprint(enc({"1": {"1": 11, "2": 12}}))
    {'1.1': 11, '1.2': 12}

    >>> pprint(enc({"1": {"1": {"1": 111}, "2": {"1": 121}}}))
    {'1.1.1': 111, '1.2.1': 121}

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

## Encoding Cfg (configparser)

    >>> from guild.util import encode_cfg

    >>> print(encode_cfg({}))

    >>> print(encode_cfg({"foo": 123}))
    [DEFAULT]
    foo = 123

    >>> print(encode_cfg({"foo": {"bar": 1.123, "baz": "hello"}, "bam": True}))
    [DEFAULT]
    bam = True
    <BLANKLINE>
    [foo]
    bar = 1.123
    baz = hello

    >>> print(encode_cfg({"foo.bar.baz": [1, 2, 3]}))
    [DEFAULT]
    foo.bar.baz = [1, 2, 3]

## File hashes

    >>> from guild.util import file_sha1, file_sha256

    >>> file_sha1(sample("textorbinary", "lena.jpg"))
    'af17f9c0a80505922933edb713bf30ec25916fbf'

    >>> file_sha256(sample("textorbinary", "lena.jpg"), use_cache=False)
    '54e97bc5e2a8744022f3c57c08d2a36566067866d9cabfbdde131e99a485134a'

## Active shell

The active shell is provided as a shell string using
`util.active_shell()`.

    >>> from guild.util import active_shell

    >>> shell = active_shell()

    >>> if shell is None:
    ...     import psutil
    ...     from guild.util import shlex_quote as _quote, _KNOWN_SHELLS
    ...     proc_path = []
    ...     p = psutil.Process().parent()
    ...     while p:
    ...         proc_path.append(_quote(p.name()))
    ...         p = p.parent()
    ...     print(f"Unknown active shell - proc path: {' < '.join(proc_path)}")
    ...     print(f"Expexted one of: {', '.join(_KNOWN_SHELLS)}")

### Active shell caching

The `util` module caches the active shell to avoid rereading the
environment. The cached value is `util._cached_active_shell`.

    >>> from guild import util
    >>> util._cached_active_shell == shell, (util._cached_active_shell, shell)
    (True, ...)

We can verify that the environment is read only when this value is set
to "__unset__". To test this, we temporarily replace the underlying
function that checks the environment (`util._active_shell`).

    >>> def _active_shell_replacement():
    ...     print("Reading the env for active shell")
    ...     return "xxx"  # value used as active shell

    >>> _active_shell_save = util._active_shell
    >>> shell_save = shell  # save value from above
    >>> util._active_shell = _active_shell_replacement

Reset the cached active shell and re-read the value.

    >>> util._cached_active_shell = "__unset__"
    >>> shell = util.active_shell()
    Reading the env for active shell

Call `active_shell()` again to verify that the environment is not read.

    >>> shell = util.active_shell()  # does not log 'Reading the env...'

    >>> shell
    'xxx'

Replace the environment read function.

    >>> util._active_shell = _active_shell_save

Force a re-read of the environment for active shell.

    >>> util._cached_active_shell = "__unset__"
    >>> shell = util.active_shell()

    >>> shell == shell_save, (shell, shell_save)
    (True, ...)

## Check Guild version

Guild `util` module provides a function to validate the current Guild
version given a package requirement spec.

    >>> from guild.util import check_guild_version
    >>> from guild import __version__ as current_guild_version

Test some version assertions that we know are true.

    >>> check_guild_version(">0.0.0")
    True

    >>> check_guild_version("<9999")
    True

Provide an invalid spec (error message varies across Python versions).

    >>> check_guild_version("not a valid spec")
    Traceback (most recent call last):
    ValueError: ...error at "'a valid '"...

Test against current verion, minus any development component.

    >>> guild_version_without_dev = re.match(
    ...     r"(\d+\.\d+\.\d+).*", current_guild_version).group(1)

    >>> check_guild_version(f"=={guild_version_without_dev}")
    True

## Format duration

    >>> from guild.util import format_duration as fd

    >>> fd(0, 0)
    '0:00:00'

    >>> fd(0, 60000000)
    '0:01:00'

    >>> fd(0, 600000000)
    '0:10:00'

    >>> fd(0, 3600000000)
    '1:00:00'

    >>> fd(0, 3601000000)
    '1:00:01'

    >>> fd(0, 3601000000.123)
    '1:00:01'

## Split lines

    >>> from guild.util import split_lines

    >>> split_lines("")
    []

    >>> split_lines("a")
    ['a']

    >>> split_lines("ab")
    ['ab']

    >>> split_lines("a\nb")
    ['a', 'b']

    >>> split_lines("\nab")
    ['ab']

    >>> split_lines("ab\n")
    ['ab']

    >>> split_lines("a\r\nb")
    ['a', 'b']

    >>> split_lines("\r\nab")
    ['ab']

    >>> split_lines("ab\r\n")
    ['ab']

    >>> split_lines("a\n\nb")
    ['a', 'b']

    >>> split_lines("\n\nab")
    ['ab']

    >>> split_lines("ab\n\n")
    ['ab']

## Converting dict keys to camel case

Use `dict_to_camel_case` to convert pascal case dict keys to camel case. This
can be used when interfacing with JavaScript applications.

    >>> from guild.util import dict_to_camel_case

    >>> dict_to_camel_case({})
    {}

    >>> pprint(dict_to_camel_case({"foo": 123, "bar": 456}))
    {'bar': 456, 'foo': 123}

    >>> pprint(dict_to_camel_case({"foo_bar": 123, "bar_baz": 456}))
    {'barBaz': 456, 'fooBar': 123}

    >>> dict_to_camel_case({"_foo": 123})
    {'_foo': 123}

    >>> dict_to_camel_case({"_foo_": 123})
    {'_foo_': 123}

    >>> dict_to_camel_case({"__foo__": 123})
    {'__foo__': 123}

    >>> dict_to_camel_case({"__foo_bar__": 123})
    {'__fooBar__': 123}

    >>> dict_to_camel_case({"__foo__bar__": 123})
    {'__foo_Bar__': 123}

    >>> dict_to_camel_case({"__foo___bar__": 123})
    {'__foo__Bar__': 123}

    >>> dict_to_camel_case({"_": 123})
    {'_': 123}

    >>> dict_to_camel_case({"__": 123})
    {'__': 123}

    >>> dict_to_camel_case({"": 123})
    {'': 123}
