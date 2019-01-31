# Batch runs - random optimizer

These tests illustrate the behavior of the random search optimizer.

The random optimizer isn't technically an optimizer as it generates
random trials without respect to an objective. It's useful however for
general exploration.

We'll use the `optimizers` project, which provides test operations for
use with optimizers.

    >>> project = sample("projects", "optimizers")

For our trials, we'll use Guild's ability to save trial information to
check the bounds of our generated trials.

Our test project is `optimizers`:

    >>> project = sample("projects", "optimizers")

Our helper, which returns a table of trials for an operation and set
of flags.

    >>> from guild import _api as gapi
    >>> import csv

    >>> def gen_trials(op, max_trials=5, **flags):
    ...     with TempFile() as csv_path:
    ...         gapi.run_capture_output(
    ...             op, flags=flags,
    ...             optimizer="random",
    ...             max_trials=max_trials,
    ...             save_trials=csv_path,
    ...             cwd=project)
    ...         rows = list(csv.reader(open(csv_path, "r")))
    ...         return rows[0], rows[1:]

We can use `echo` as our operation (we won't actually run the
operation - it's just used for generating trials).

    >>> gf = guildfile.from_dir(project)
    >>> echo_op = gf.default_model.get_operation("echo")

    >>> echo_op.name
    'echo'

    >>> pprint(echo_op.flag_values())
    {'x': 1.0, 'y': 2, 'z': 'a'}

For the tests below, note the min and max values for `x`:

    >>> x_flag = echo_op.get_flagdef("x")
    >>> x_flag.min
    -2.0
    >>> x_flag.max
    2.0

Note also that `z` defines choices:

    >>> z_flag = echo_op.get_flagdef("z")
    >>> z_choices = [c.value for c in z_flag.choices]
    >>> z_choices
    ['a', 'b', 'c', 'd']

At the moment, when we run `echo` with random without additional
information, random uses the default flags for each trial.

    >>> flags, trials = gen_trials("echo")
    >>> flags
    ['x', 'y', 'z']

    >>> len(trials)
    5

    >>> trials
    [['...', '2', '...'],
     ['...', '2', '...'],
     ['...', '2', '...'],
     ['...', '2', '...'],
     ['...', '2', '...']]

The values for `x` and `z` are not known because they are generated at
random. However, we can check their bounds to make sure they are
within the prescribed min and max (see above).

Here's a helper function:

    >>> def check_echo_trials(trials, x_min, x_max, z_vals):
    ...     print("Checking %i trials" % (len(trials)))
    ...     for row in trials:
    ...         x = float(row[0])
    ...         if x < x_min or x > x_max:
    ...             print("x is out of range: %s" % x)
    ...         z = row[2]
    ...         if z not in z_vals:
    ...             print("unexpected value for z: %s" % z)

Let's check x:

    >>> check_echo_trials(trials, x_flag.min, x_flag.max, z_choices)
    Checking 5 trials

We can specify flags for the run, which override those defined in the
Guild file.

Here's a run that doesn't use any random flags - each flag value is a
scalar:

    >>> _, trials = gen_trials("echo", x=1.0, y=2.1, z="d")

    >>> len(trials)
    5

    >>> trials
    [['1.0', '2.1', 'd'],
     ['1.0', '2.1', 'd'],
     ['1.0', '2.1', 'd'],
     ['1.0', '2.1', 'd'],
     ['1.0', '2.1', 'd']]

Let's experiment with some different changes, specified as flags:

    >>> _, trials = gen_trials("echo", x="[-0.1:0.1]", y="hat", z=["a","b"])

    >>> len(trials)
    5

    >>> trials
    [['...', 'hat', '...'],
     ['...', 'hat', '...'],
     ['...', 'hat', '...'],
     ['...', 'hat', '...'],
     ['...', 'hat', '...']]

And let's check the range:

    >>> check_echo_trials(trials, -0.1, 0.1, ["a", "b"])
    Checking 5 trials
