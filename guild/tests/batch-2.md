# Batch runs - part 2

[Part 1](batch-1.md) illustrated basic grid search. These tests look
at the random search features of Guild batch runs.

There are two applications of random search in Guild's batch facility:

- Random trials selected when runs are limited
- Flag distribution values

## Max runs and random search

When Guild runs a batch, it generates trials by computing the
cartesian product of flag list values. This is illustrated in detail
in [Part 1](batch-1.md).

The number of generated trials can be limited using the `--max-runs`
run option. If the max runs is less than the number of generated
trials, Guild will select at random trials to omit in order to stay
within the specified maximum.
