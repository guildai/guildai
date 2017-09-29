# Tables

Support for printing tables to stdout is provided by the `table`
module:

    >>> import guild.cli

Sample data:

    >>> data = [
    ...    {"name": "Bob", "age": 23},
    ...    {"name": "Mary", "age": 34},
    ...    {"name": "Greg", "age": 45},
    ... ]

Two columns, ordered by age:

    >>> guild.cli.table(data, ["name", "age"], "age")
    Bob   23
    Mary  34
    Greg  45

Two columns, reverse ordered by age:

    >>> guild.cli.table(data, ["name", "age"], "-age")
    Greg  45
    Mary  34
    Bob   23

Two columns, ordered by name:

    >>> guild.cli.table(data, ["name", "age"], "name")
    Bob   23
    Greg  45
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
    45  Greg

Name with age details:

    >>> guild.cli.table(data, ["name"], detail=["age"])
    Bob
      age: 23
    Mary
      age: 34
    Greg
      age: 45
