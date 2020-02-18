# Guild Example: `api`

This example shows the use of the `guild.ipy` module as an API for
interfacing with Guild runs. A sample operation uses the API to find
matching runs and perform a summary action.

- [guild.yml](guild.yml) - Project Guild file
- [op.py](op.py) - Sample operation
- [summary.py](summary.py) - Sample summary operation

For more examples of using `guild.ipy`, see the
[`notebooks`](../notebooks/README.md) example.

To run the example, generate some sample runs:

```
$ guild run op x=linspace[-2:2:9]
```

Then run `summary`:

```
$ guild run summary
```

`summary` prints the runs that meet the `min-loss` criterion. It also
creates symlinks to those runs. View the links:

```
$ guild runs ls
```

Use a modified version of [`summary.py`](summary.py) as needed:

- Change the operations and selection criteria
- Change how each run is summarized
