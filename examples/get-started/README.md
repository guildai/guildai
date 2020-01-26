# Guild Example: `get-started`

This example is from [Guild Get Started](https://guild.ai/start).

- [train.py](train.py) - Mock training script.

## Single Runs

Run the script directly:

```
$ guild run train.py
```

Specify a value for `x`:

```
$ guild run train.py x=1.0
```

## Bayesian Optimization

Run an optimzation batch to find values for `x` that minimize `loss`:

```
$ guild run train.py x=[-2.0:2.0] --optimize
```

Restart the batch to run more trials:

```
$ guild run --restart $(guild select -o train.py+gp) -Fo random-starts=0
```

## Grid Search

Run 10 trials where x is evently spaced between `-1.0` and `1.0`:

```
$ guild run train.py x=linspace[-1:1:10]
```

Use TensorBoard to view the last 10 runs:

```
guild tensorboard 1:10
```

Click **HPARAMS** at the top of the page and then click **SCATTER PLOT
MATRIX VIEW**. Find the plot of `loss` against `x` and note the lowest
`loss` is where `x` is near `0.3`.
