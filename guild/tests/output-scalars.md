# Output Scalars

These tests demonstrate the function in `guild.summary` regarding
output scalars.

    >>> from guild.summary import OutputScalars

Helper to test patterns and input lines.

    >>> def apply_lines(patterns, lines):
    ...   class Writer:
    ...     def __init__(self):
    ...       self.scalars = []
    ...
    ...     def add_scalar(self, tag, val, step):
    ...       self.scalars.append((tag, val, step))
    ...
    ...     def flush(self):
    ...       pass
    ...
    ...   NOT_USED = object()
    ...   outs = OutputScalars(patterns, NOT_USED)
    ...   outs._writer = Writer()
    ...   for line in lines.split("\n"):
    ...     outs.write(line)
    ...   for scalar in outs._writer.scalars:
    ...     print(scalar)

## Default output scalars

Default output scalars are defined in
`summary.DEFAULT_OUTPUT_SCALARS`. These capture scalars in the pattern
`<key>: <value>` and `<key>: <value> (<step>)`.

    >>> from guild.summary import DEFAULT_OUTPUT_SCALARS

For simple, non-repeating keys without a step, Guild uses the default
step of `0`.

    >>> apply_lines(DEFAULT_OUTPUT_SCALARS, """
    ... x: 1.1
    ... y: 1.2
    ... z: 1.3
    ... """)
    ('x', 1.1, 0)
    ('y', 1.2, 0)
    ('z', 1.3, 0)

If a step is provided, Guild captures that value and does not provide
a default.

    >>> apply_lines(DEFAULT_OUTPUT_SCALARS, """
    ... x: 1.1 (10)
    ... y: 1.2 (10)
    ... z: 1.3 (10)
    ... """)
    ('x', 1.1, 10.0)
    ('y', 1.2, 10.0)
    ('z', 1.3, 10.0)

When a key repeats, Guild increments the step by 1.

    >>> apply_lines(DEFAULT_OUTPUT_SCALARS, """
    ... x: 1.1
    ... x: 1.2
    ... x: 1.3
    ... """)
    ('x', 1.1, 0)
    ('x', 1.2, 1)
    ('x', 1.3, 2)

    >>> apply_lines(DEFAULT_OUTPUT_SCALARS, """
    ... x: 1.1
    ... y: 2.2
    ... x: 3.3
    ... y: 4.4
    ... x: 5.5
    ... y: 6.6
    ... """)
    ('x', 1.1, 0)
    ('y', 2.2, 0)
    ('x', 3.3, 1)
    ('y', 4.4, 1)
    ('x', 5.5, 2)
    ('y', 6.6, 2)

Any repeated key causes the step to increment.

    >>> apply_lines(DEFAULT_OUTPUT_SCALARS, """
    ... x: 1.1
    ... y: 2.2
    ... y: 3.3
    ... y: 4.4
    ... x: 5.5
    ... y: 6.6
    ... """)
    ('x', 1.1, 0)
    ('y', 2.2, 0)
    ('y', 3.3, 1)
    ('y', 4.4, 2)
    ('x', 5.5, 2)
    ('y', 6.6, 3)

Any any point a step may be specified, at which point Guild steps
auto-incrementing based on repeat values.

    >>> apply_lines(DEFAULT_OUTPUT_SCALARS, """
    ... x: 1.1
    ... y: 2.2
    ... x: 3.3
    ... y: 4.4 (10)
    ... x: 5.5
    ... y: 6.6
    ... """)
    ('x', 1.1, 0)
    ('y', 2.2, 0)
    ('x', 3.3, 1)
    ('y', 4.4, 10.0)
    ('x', 5.5, 10.0)
    ('y', 6.6, 10.0)
