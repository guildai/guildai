# Tables

Support for printing tables to stdout is provided by the `table`
module:

    >>> import guild.cli

Sample data:

    >>> data = [
    ...    {"name": "Bob", "age": 23},
    ...    {"name": "Mary", "age": 34},
    ...    {"name": "Greg", "age": None},
    ... ]

Two columns, ordered by age:

    >>> guild.cli.table(data, ["name", "age"], "age")
    Greg
    Bob   23
    Mary  34

Two columns, reverse ordered by age:

    >>> guild.cli.table(data, ["name", "age"], "-age")
    Mary  34
    Bob   23
    Greg

Two columns, ordered by name:

    >>> guild.cli.table(data, ["name", "age"], "name")
    Bob   23
    Greg
    Mary  34

One columns, unordered:

    >>> guild.cli.table(data, ["name"])
    Bob
    Mary
    Greg

Two columns, unordered:

    >>> guild.cli.table(data, ["age", "name"])
    23  Bob
    34  Mary
        Greg

Name with age details:

    >>> guild.cli.table(data, ["name"], detail=["age"])
    Bob
      age: 23
    Mary
      age: 34
    Greg
      age:

## Item compare

Tables support sorting rows on columns that may contain different
value types. The tests below demonstrate the private `_val_cmp`
function, which is responsible for comparing two values of arbitrary
type.

    >>> _cmp = cli._val_cmp

Same type:

    >>> _cmp({"x": 1}, {"x": 1}, "x")
    0

    >>> _cmp({"x": 1}, {"x": 2}, "x")
    -1

    >>> _cmp({"x": 2}, {"x": 1}, "x")
    1

Ints and floats:

    >>> _cmp({"x": 1}, {"x": 1.0}, "x")
    0

    >>> _cmp({"x": 1}, {"x": 1.1}, "x")
    -1

    >>> _cmp({"x": 1.1}, {"x": 1}, "x")
    1

None values:

    >>> _cmp({"x": None}, {"x": None}, "x")
    0

    >>> _cmp({"x": None}, {"x": "a"}, "x")
    -1

    >>> _cmp({"x": "a"}, {"x": None}, "x")
    1

    >>> _cmp({"x": None}, {"x": 1}, "x")
    -1

    >>> _cmp({"x": 1}, {"x": None}, "x")
    1

Strings and numbers:

    >>> _cmp({"x": "1"}, {"x": 1}, "x")
    1

    >>> _cmp({"x": 1}, {"x": "1"}, "x")
    -1
