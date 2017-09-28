# Guild and Pandas DataFrame

Guild uses Pandas DataFrames internally to implement various
features. These tests illustrate DataFrame behavior.

>>> import pandas
>>> pandas.DataFrame({
...    "x": [1, 2, 3],
...    "y": [4, 5, 6]})
       x  y
    0  1  4
    1  2  5
    2  3  6
