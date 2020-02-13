# Guild Example: `features`

This is an experimental example to show how one might use flags to
enable features for testing.

- [switch.py](switch.py) - Uses boolean switches to enable features
- [bitmap.py](bitmap.py) - Uses a bitmap to enable features

## Switches

[switch.py](switch.py) defines each feature as a boolean switch. A
full search over all feature combinations is run by specifying both on
and off for each feature.

```
$ guild run switch.py a=[on,off] b=[on,off] c=[on,off]
```

This approach is intuitive and has the advantage of showing enabled
features as flags for comparison. However, it doesn't scale for large
numbers of features.

## Bitmap

[bitmap.py](bitmap.py) uses a single `features` flag that is a bitmap
of enabled features.

Features are selected by specifying a value for `features` that
enables the feature bit (little-endian in this case).

Use the `range` function to generate a sequence of integers for each
bitmap value.

For example, to run a full search with each feature combination for 3
features, use:

```
$ guild run bitmap.py feature_count=3 features=range[8]
```

`range[8]` generates a sequence of integers from 0 to 7, representing
each of the possible feature bitmaps for three features (2 ^ 3).

This approach scales well for large numbers of features. However, it's
not easy to compare selected features across runs.
