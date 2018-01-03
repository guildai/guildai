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

IO Errors are passed through:

    >>> try:
    ...   is_text("non-existing")
    ... except IOError:
    ...   print("Not found!")
    Not found!

Directories aren't text files:

    >>> is_text(".")
    False
