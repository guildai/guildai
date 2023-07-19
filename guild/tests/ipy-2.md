# Interactive Python interface, part 2

These tests demonstrate the `ipy` interface applied to various
generated runs.

## Run attributes

    >>> use_project("run-attrs")

    >>> run("guild run logged -y")
    <exit 0>

    >>> run("guild run logged-core -y -l 'Real label'")
    <exit 0>

    >>> from guild import ipy

    >>> ipy.runs()
       run   operation started    status label
    0  ... logged-core     ... completed Real label
    1  ...      logged     ... completed

    >>> ipy.runs().attributes()
               custom-id            custom-label   id                  label opdef-attr logged-1                                 logged-2
    0  This attr is okay  This attr is also okay  bbb  Trying to log a label        NaN      NaN                                      NaN
    1                NaN                     NaN  NaN                    NaN        red    green  {"numbers": [1, 3, 5], "color": "blue"}

    >>> ipy.runs().compare()
       run    operation  started    time     status       label          custom-id            custom-label   id       label logged-1                                 logged-2 opdef-attr
    0  ...  logged-core      ...  0 days  completed  Real label  This attr is okay  This attr is also okay  bbb  Real label      NaN                                      NaN        NaN
    1  ...       logged      ...  0 days  completed                            NaN                     NaN  NaN                green  {"numbers": [1, 3, 5], "color": "blue"}        red
