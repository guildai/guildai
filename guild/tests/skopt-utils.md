# skopt utils

Various skopt related utilities are provided by
`guild.plugins.skopt_util`:

    >>> from guild.plugins import skopt_util

## skopt dims from flags

Flag values can be converted to skopt dims using the `flag_dims`
function:

    >>> flag_dims = skopt_util.flag_dims

The function returns a tuple of dim names, dims, and initial values
that correspond to the flags.

Here's the empty case:

    >>> flag_dims({})
    ([], [], [])

Non-list values are always returned as categorical with a single
element:

    >>> flag_dims({"a": 1})
    (['a'], [Categorical(categories=(1,), prior=None)], [1])

    >>> flag_dims({"a": 2.1})
    (['a'], [Categorical(categories=(2.1,), prior=None)], [2.1])

    >>> flag_dims({"a": "hello"})
    (['a'], [Categorical(categories=('hello',), prior=None)], ['hello'])

Lists are always returned as categorical containing the list values:

    >>> flag_dims({"a": [1, 2, 3]})
    (['a'], [Categorical(categories=(1, 2, 3), prior=None)], [None])

    >>> flag_dims({"a": [1, 2.1, "hello"]})
    (['a'], [Categorical(categories=(1, 2.1, 'hello'), prior=None)], [None])

### Functions

It starts getting interesting when we provide functions, which are in
the format:

    NAME? '[' ARG ':' ARG ( ':' ARG )* ']'

If unnamed, a function is assumed to be named "uniform":

    >>> flag_dims({"a": "[1.0:2.0]"})
    (['a'], [Real(low=1.0, high=2.0, prior='uniform', transform='identity')], [None])

A third argument may be provided, which is used as the initial value:

    >>> flag_dims({"a": "[1.0:2.0:0.0]"})
    (['a'], [Real(low=1.0, high=2.0, prior='uniform', transform='identity')], [0.0])

If two integers are provided, the range is over integer values:

    >>> flag_dims({"a": "[1:100]"})
    (['a'], [Integer(low=1, high=100)], [None])

Two integers with an initial value:

    >>> flag_dims({"a": "[1:100:50]"})
    (['a'], [Integer(low=1, high=100)], [50])

We can name functions, provided the function is supported:

- uniform

    >>> flag_dims({"a": "uniform[1.0:2.0]"})
    (['a'], [Real(low=1.0, high=2.0, prior='uniform', transform='identity')], [None])

    >>> flag_dims({"a": "uniform[1:100]"})
    (['a'], [Integer(low=1, high=100)], [None])

    >>> flag_dims({"a": "uniform[1:100:25]"})
    (['a'], [Integer(low=1, high=100)], [25])

- loguniform

    >>> flag_dims({"a": "loguniform[1.0:2.0]"})
    (['a'], [Real(low=1.0, high=2.0, prior='log-uniform', transform='identity')], [None])

    >>> flag_dims({"a": "loguniform[1.0:2.0:0.1]"})
    (['a'], [Real(low=1.0, high=2.0, prior='log-uniform', transform='identity')], [0.1])

    >>> flag_dims({"a": "loguniform[1:100]"})
    (['a'], [Real(low=1, high=100, prior='log-uniform', transform='identity')], [None])

Note that normal and lognormal are not supported:

    >>> flag_dims({"a": "normal[1.0:2.0]"})
    Traceback (most recent call last):
    BatchError: unsupported function 'normal' for flag a

    >>> flag_dims({"a": "lognormal[1.0:2.0]"})
    Traceback (most recent call last):
    BatchError: unsupported function 'lognormal' for flag a

If an unsupported function is specified, an error is generated:

    >>> flag_dims({"a": "unsupported[1.0:2.0]"})
    Traceback (most recent call last):
    BatchError: unsupported function 'unsupported' for flag a

If a function has the wrong arg count, an error is generated:

    >>> flag_dims({"a": "uniform[]"})
    Traceback (most recent call last):
    BatchError: uniform requires 2 or 3 args, got () for flag a

    >>> flag_dims({"a": "uniform[1.0]"})
    Traceback (most recent call last):
    BatchError: uniform requires 2 or 3 args, got (1.0,) for flag a

    >>> flag_dims({"a": "uniform[1.0:2.0:3.0:4.0]"})
    Traceback (most recent call last):
    BatchError: uniform requires 2 or 3 args, got (1.0, 2.0, 3.0, 4.0) for flag a

If a function doesn't meet the minimal requirement of a function
(i.e. it must contain at least two args)

### Misc

Dims are always returned in sorted order by name:

    >>> flag_dims({"a": 3, "b": 2, "c": 1})
    (['a', 'b', 'c'],
     [Categorical(categories=(3,), prior=None),
      Categorical(categories=(2,), prior=None),
      Categorical(categories=(1,), prior=None)],
     [3, 2, 1])
