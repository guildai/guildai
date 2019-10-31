# Train missing model

Guild will display an error message if you try to run an operation on
a model it can't find.

    >>> run("guild run -y logreg:train epochs=1")
    guild: cannot find operation logreg:train
    Try 'guild operations' for a list of available operations.
    <exit 1>
