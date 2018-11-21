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

A map of vals may contain references to other vals. Use
`resolve_all_refs` to resolve all references in the map.

    >>> from guild.util import resolve_all_refs as resolve

No references:

    >>> resolve({"a": 1})
    {'a': 1}

    >>> resolve({"a": "1"})
    {'a': '1'}

Reference to undefined value:

    >>> resolve({"a": "${b}"})
    Traceback (most recent call last):
    UndefinedReferenceError: b

    >>> resolve({"a": "${b}"}, undefined="foo")
    {'a': 'foo'}

Reference to a value:

    >>> pprint(resolve({"a": "${b}", "b": 1}))
    {'a': 1, 'b': 1}

Reference to a value with a reference:

    >>> pprint(resolve({"a": "${b}", "b": "${c}", "c": 1}))
    {'a': 1, 'b': 1, 'c': 1}

Reference embedded in a string:

    >>> pprint(resolve({"a": "b equals ${b}", "b": 1}))
    {'a': 'b equals 1', 'b': 1}

    >>> resolve(
    ... {"msg": "${x} + ${y} = ${z}",
    ...  "x": "one",
    ...  "y": "two",
    ...  "z": "three"})["msg"]
    'one + two = three'

Reference cycle:

    >>> resolve({"a": "${b}", "b": "${a}"})
    Traceback (most recent call last):
    ReferenceCycleError: ['b', 'a', 'b']

Resolving non string values:

    >>> resolve({
    ...   "msg": "${i} ${f} ${none}",
    ...   "i": 1,
    ...   "f": 1.2345,
    ...   "none": None})["msg"]
    '1 1.2345 null'

Note that None is resolved as 'null' for consistency with flag inputs,
which convert the string 'null' into None.

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

    >>> is_text("hello_world.py")
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

A non-existing file is considered not test:

    >>> is_text("non-existing")
    False

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
    [(1524584359781, 0, u'Tue Apr 24 10:39:19 CDT 2018'),
     (1524584364782, 0, u'Tue Apr 24 10:39:24 CDT 2018'),
     (1524584369785, 0, u'Tue Apr 24 10:39:29 CDT 2018'),
     (1524584374790, 0, u'Tue Apr 24 10:39:34 CDT 2018')]

We can alternatively read using start and end indices.

    >>> reader.read(0, 0)
    [(1524584359781, 0, u'Tue Apr 24 10:39:19 CDT 2018')]

    >>> reader.read(1, 1)
    [(1524584364782, 0, u'Tue Apr 24 10:39:24 CDT 2018')]

    >>> reader.read(2, 3)
    [(1524584369785, 0, u'Tue Apr 24 10:39:29 CDT 2018'),
     (1524584374790, 0, u'Tue Apr 24 10:39:34 CDT 2018')]

If start is omitted, output is read form the start.

    >>> reader.read(end=2)
    [(1524584359781, 0, u'Tue Apr 24 10:39:19 CDT 2018'),
     (1524584364782, 0, u'Tue Apr 24 10:39:24 CDT 2018'),
     (1524584369785, 0, u'Tue Apr 24 10:39:29 CDT 2018')]

If end is omitted, output is read to the end.

    >>> reader.read(start=2)
    [(1524584369785, 0, u'Tue Apr 24 10:39:29 CDT 2018'),
     (1524584374790, 0, u'Tue Apr 24 10:39:34 CDT 2018')]

When we're run reading we can close the reader:

    >>> reader.close()

## Label templates

The function `render_label` is used to render strings in the
label template syntax.

    >>> from guild.util import render_label as render

Examples:

    >>> render("", {})
    ''

    >>> render("hello", {})
    'hello'

    >>> render("a-${b}-c", {})
    'a--c'

    >>> render("${b}-c", {})
    '-c'

    >>> render("a-${b}", {})
    'a-'

    >>> render("a-${b|default:b}-c", {})
    'a-b-c'

    >>> render("${b|default:b}-c", {})
    'b-c'

    >>> render("a-${b|default:b}", {})
    'a-b'

    >>> render("a-${b}-c", {"b": "b"})
    'a-b-c'

    >>> render("${b}-c", {"b": "b"})
    'b-c'

    >>> render("a-${b}", {"b": "b"})
    'a-b'

    >>> render("${path|basename}", {"path": "foo/bar.txt"})
    'bar.txt'

    >>> render("${path|basename}", {})
    ''

A typical label:

    >>> render("${trained-model}-${step|default:latest}", {
    ...   "trained-model": "abcd1234",
    ...   "step": "1234"
    ... })
    'abcd1234-1234'

    >>> render("${trained-model}-${step|default:latest}", {
    ...   "trained-model": "abcd1234"
    ... })
    'abcd1234-latest'

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
