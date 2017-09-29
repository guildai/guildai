# Tables

>>> import guild.table

>>> data = [
...    {"name": "Bob", "age": 23},
...    {"name": "Mary", "age": 34},
...    {"name": "Greg", "age": 45},
... ]

>>> guild.table.out(data, ["name", "age"], "age")
Bob   23
Mary  34
Greg  45

>>> guild.table.out(data, ["name", "age"], "-age")
Greg  45
Mary  34
Bob   23

>>> guild.table.out(data, ["name", "age"], "name")
Bob   23
Greg  45
Mary  34

>>> guild.table.out(data, ["name"])
Bob
Mary
Greg
