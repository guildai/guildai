# skopt utils

Various skopt related utilities are provided by
`guild.plugins.skopt_util`:

    >>> from guild.plugins import skopt_util

## skopt dims from flags

Flag values can be converted to skopt dims using the `flag_dims`
function:

    >>> flag_dims = skopt_util.flag_dims

The function returns a tuple of dim names and corresponding dim values
that can be used with the skopt minimize functions.

Here's the empty case:

    >>> flag_dims({})
    ([], [])

Non-list values are always returned as categorical with a single
element:

    >>> flag_dims({"a": 1})
    (['a'], [Categorical(categories=(1,), prior=None)])

    >>> flag_dims({"a": 2.1})
    (['a'], [Categorical(categories=(2.1,), prior=None)])

    >>> flag_dims({"a": "hello"})
    (['a'], [Categorical(categories=('hello',), prior=None)])

Lists are always returned as categorical containing the list values:

    >>> flag_dims({"a": [1, 2, 3]})
    (['a'], [Categorical(categories=(1, 2, 3), prior=None)])

    >>> flag_dims({"a": [1, 2.1, "hello"]})
    (['a'], [Categorical(categories=(1, 2.1, 'hello'), prior=None)])

### Functions

It starts getting interesting when we provide functions, which are in
the format:

    NAME? '[' ARG ':' ARG ( ':' ARG )* ']'

If unnamed, a function is assumed to be named "uniform":

    >>> flag_dims({"a": "[1.0:2.0]"})
    (['a'], [Real(low=1.0, high=2.0, prior='uniform', transform='identity')])

If two integers are provided, the range is over integer values:

    >>> flag_dims({"a": "[1:100]"})
    (['a'], [Integer(low=1, high=100)])

We can name functions, provided the function is supported:

- uniform

    >>> flag_dims({"a": "uniform[1.0:2.0]"})
    (['a'], [Real(low=1.0, high=2.0, prior='uniform', transform='identity')])

    >>> flag_dims({"a": "uniform[1:100]"})
    (['a'], [Integer(low=1, high=100)])

- loguniform

    >>> flag_dims({"a": "loguniform[1.0:2.0]"})
    (['a'], [Real(low=1.0, high=2.0, prior='log-uniform', transform='identity')])

    >>> flag_dims({"a": "loguniform[1:100]"})
    (['a'], [Real(low=1, high=100, prior='log-uniform', transform='identity')])

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
    BatchError: uniform requires 2 arg(s), got ()

    >>> flag_dims({"a": "uniform[1.0]"})
    Traceback (most recent call last):
    BatchError: uniform requires 2 arg(s), got (1.0,)

    >>> flag_dims({"a": "uniform[1.0:2.0:3.0]"})
    Traceback (most recent call last):
    BatchError: uniform requires 2 arg(s), got (1.0, 2.0, 3.0)

If a function doesn't meet the minimal requirement of a function
(i.e. it must contain at least two args)
