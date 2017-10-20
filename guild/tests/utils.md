# Guild utils

## Matching filters

    >>> from guild.util import match_filter

Empty case:

    >>> match_filter([], [])
    True

One filter for empty vals:

    >>> match_filter(["a"], [])
    False

No filters for vals:

    >>> match_filter([], ["a"])
    True

One filter matching one val:

    >>> match_filter(["a"], ["a"])
    True

One filter not matching one val:


    >>> match_filter(["a"], ["b"])
    False

One filter matching one of two vals:

    >>> match_filter(["a"], ["b", "a"])
    True

Two filters for empty vals:

    >>> match_filter(["a", "b"], [])
    False

Two filters for one matching where match_any is False (default):

    >>> match_filter(["a", "b"], ["a"])
    False

Two filters for one matching valwhere match_any is True:

    >>> match_filter(["a", "b"], ["a"], match_any=True)
    True

Two filters matching both vals:

    >>> match_filter(["a", "b"], ["a", "b"])
    True

Two filters matching both vals (alternate order);

    >>> match_filter(["a", "b"], ["b", "a"])
    True
