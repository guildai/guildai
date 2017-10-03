# Var support

The module `var` provides support for listing and managing content
under the Guild "var" directory - i.e. the directory containing system
wide Guild generated content.

    >>> import guild.var

## Filtering runs

These tests exercise the low-level filtering used when filtering runs.

Filtering applies a condition to each run to test whether or not it
should be included in the result set.

Filtering is currently limited to two simple conditions:

 - Test if all conditions are met (a list of conditions)

 - Test if an attribute equals a value (a two-tuple of name and
   expected value)

 - Test if an attribute satisfies a boolean condition (a three-tuple
   of name, condition, and value where condition is "=" or "!=")

This scheme will be extended as more filter capabilities are added.

For testing purposes, we'll create a set of objects that mimic the
`guild.run.Run` interface.

    >>> class Run(object):
    ...
    ...   def __init__(self, id, attrs):
    ...     self.id = id
    ...     self.attrs = attrs
    ...
    ...   def __repr__(self):
    ...     return "<Run '%s'>" % self.id
    ...
    ...   def get(self, name):
    ...     return self.attrs.get(name)

    >>> runs = [
    ...   Run("a", {"op": "train", "exit_status": "0"}),
    ...   Run("b", {"op": "train", "exit_status": "1"}),
    ...   Run("c", {"op": "test", "exit_status": "0"}),
    ...   Run("d", {"op": "train"}),
    ...   Run("e", {"op": "train", "exit_status": "0"}),
    ... ]

Next we'll create a function that will filter a list of runs given a
filter spec:

    >>> def filter_runs(run_filter):
    ...   return [run for run in runs if run_filter(run)]

    >>> run_filter = guild.var.run_filter

### All runs

    >>> filter_runs(run_filter("true"))
    [<Run 'a'>, <Run 'b'>, <Run 'c'>, <Run 'd'>, <Run 'e'>]

### exit_status is "0"

    >>> filter_runs(run_filter("attr", "exit_status", "0"))
    [<Run 'a'>, <Run 'c'>, <Run 'e'>]

### exit_status is not "0"

    >>> filter_runs(run_filter("!attr", "exit_status", "0"))
    [<Run 'b'>, <Run 'd'>]

### op is "train" and exit_status is "0"

    >>> filter_runs(
    ...   run_filter("all", [
    ...     run_filter("attr", "op", "train"),
    ...     run_filter("attr", "exit_status", "0"),
    ...   ]))
    [<Run 'a'>, <Run 'e'>]

### op is "train" and exit_status is not "0"

    >>> filter_runs(
    ...   run_filter("all", [
    ...     run_filter("attr", "op", "train"),
    ...     run_filter("!attr", "exit_status", "0"),
    ...   ]))
    [<Run 'b'>, <Run 'd'>]
