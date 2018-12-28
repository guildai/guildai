# Query

These are notes for a generalized query facility.

This facility would likely replace the compare feature.

It might entain a new `query` command or reuse the `compare` command.

A generalized query facility could in theory do more than compare, so
perhaps we should go with that during the R&D phase.

## Selecting columns

The following examples use an enhanced version of `compare` to show
columns using a new `-c, --columns` option.

This would be used to display the latest 'loss' scalar:

    $ guild compare -c loss

This would yield something like this:

    run       model       operation  started              time     status     label  loss
    cab46e0a  mnist_irnn  train      2018-12-27 07:03:23  0:07:16  running           2.102782
    db5855ec  mnist_mlp   train      2018-12-27 06:56:41  0:01:12  completed         0.029481

The `--columns` option could contain a comma separated list. It would
accept a valid column spec list as supported by `guild.query` (see
[query-parser.md](guild/tests/query-parser.md) for examples).

    $ guild compare -c "loss, val_acc, acc as train_acc"

This would add the specified scalars to the end of the display. The
`acc` scalar would be named as `train_acc`.

A qualifier of `min`, `max`, `first`, or `last` may be specified for a
scalar column:

    $ guild compare -c "min loss"

A keyword `step` may be specified

In addition to scalars (default) columns may be flags or run
attributes. The following table lists syntax used for each column
type.

| Type   | Prefixes         | Qualifiers         | Step |
|--------|------------------|--------------------|------|
| scalar | (none) `scalar:` | min max first last | yes  |
| attr   | `.` `attr:`      |                    | no   |
| flag   | `=` `flag:`      |                    | no   |
| output | `output:`        | min max first last | no   |

The option `-s, --strict-columns` (or something along those lines)
would only show the specified columns. Run attrs are specified using
`.NAME` or `attr:NAME` syntax.

For example, to replicate the command `guild compare -c loss` using
strict columns, use:

    $ guild compare -s ".run, .model, .operation, .started,
                        .time, .status, .label, loss"
