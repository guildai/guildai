# Model help

Model help support is provided by `guild.help`.

    >>> import guild.help

It's used to format help for a guildfile.

    >>> gf = guildfile.from_dir(sample("projects/mnist-pkg"))

The `package_description` function returns a restructured text
formatted string:

    >>> print(guild.help.package_description(gf)) # doctest: +REPORT_UDIFF
    Models
    ######
    <BLANKLINE>
    expert
    ======
    <BLANKLINE>
    *Expert model*
    <BLANKLINE>
    Operations
    ^^^^^^^^^^
    <BLANKLINE>
    evaluate
    --------
    Flags
    `````
    <BLANKLINE>
    **batch-size**
      *Number of images per eval batch (default is 50000)*
    <BLANKLINE>
    **epochs**
      *Epochs to evaluate (default is 1)*
    <BLANKLINE>
    train
    -----
    Flags
    `````
    <BLANKLINE>
    **batch-size**
      *Number of images per train batch (default is 100)*
    <BLANKLINE>
    **clones**
      *Number of clones to deploy to (default is calculated)*
    <BLANKLINE>
    **epochs**
      *Number of epochs to train (default is 5)*
    <BLANKLINE>
    **learning-rate**
      *Learning rate for training (default is 0.001)*
    <BLANKLINE>
    <BLANKLINE>
    intro
    =====
    <BLANKLINE>
    Operations
    ^^^^^^^^^^
    <BLANKLINE>
    evaluate
    --------
    Flags
    `````
    <BLANKLINE>
    **batch-size**
      *Number of images per eval batch (default is 50000)*
    <BLANKLINE>
    **epochs**
      *Epochs to evaluate (default is 2)*
    <BLANKLINE>
    train
    -----
    Flags
    `````
    <BLANKLINE>
    **batch-size**
      *Number of images per train batch (default is 100)*
    <BLANKLINE>
    **clones**
      *Number of clones to deploy to (default is calculated)*
    <BLANKLINE>
    **epochs**
      *Number of epochs to train (default is 10)*
    <BLANKLINE>
    **learning-rate**
      *Learning rate for training (default is 0.001)*
    <BLANKLINE>
    References
    ^^^^^^^^^^
    <BLANKLINE>
    - https://www.tensorflow.org/tutorials/layers
    <BLANKLINE>
