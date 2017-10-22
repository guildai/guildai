# Train missing model

Guild will display an error message if you try to run an operation on
a model it can't find.

    >>> run("guild train -y mnist-softmax epochs=1")
    guild: cannot find a model matching 'mnist-softmax'
    Try 'guild models' for a list of available models.
    <exit 1>
