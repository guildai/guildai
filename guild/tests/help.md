# Model help

Model help support is provided by `guild.help`.

    >>> import guild.help

It's used to format help for a guildfile.

    >>> from guild import guildfile
    >>> gf = guildfile.from_dir(sample("projects/mnist"))

The `package_description` function returns a restructured text
formatted string:

    >>> print(guild.help.package_description(gf)) # doctest: +REPORT_UDIFF
    Models
    ######
    <BLANKLINE>
    expert
    ######
    <BLANKLINE>
    *Expert model*
    <BLANKLINE>
    Operations
    ==========
    <BLANKLINE>
    evaluate
    ^^^^^^^^
    Flags
    -----
    <BLANKLINE>
    **batch-size**
      *Number of images per eval batch (50000)*
    <BLANKLINE>
    **epochs**
      *Epochs to evaluate (1)*
    <BLANKLINE>
    train
    ^^^^^
    Flags
    -----
    <BLANKLINE>
    **batch-size**
      *Number of images per train batch (100)*
    <BLANKLINE>
    **clones**
      *Number of clones to deploy to (calculated)*
    <BLANKLINE>
    **epochs**
      *Number of epochs to train (5)*
    <BLANKLINE>
    **learning-rate**
      *Learning rate for training (0.001)*
    <BLANKLINE>
    <BLANKLINE>
    intro
    #####
    <BLANKLINE>
    Operations
    ==========
    <BLANKLINE>
    evaluate
    ^^^^^^^^
    Flags
    -----
    <BLANKLINE>
    **batch-size**
      *Number of images per eval batch (50000)*
    <BLANKLINE>
    **epochs**
      *Epochs to evaluate (2)*
    <BLANKLINE>
    train
    ^^^^^
    Flags
    -----
    <BLANKLINE>
    **batch-size**
      *Number of images per train batch (100)*
    <BLANKLINE>
    **clones**
      *Number of clones to deploy to (calculated)*
    <BLANKLINE>
    **epochs**
      *Number of epochs to train (10)*
    <BLANKLINE>
    **learning-rate**
      *Learning rate for training (0.001)*
    <BLANKLINE>
    References
    ==========
    <BLANKLINE>
    - https://www.tensorflow.org/tutorials/layers
    <BLANKLINE>
