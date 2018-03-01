# Model help

    >>> import guild.help

    >>> from guild import guildfile

    >>> gf = guildfile.from_dir(sample("projects/mnist"))
    >>> print(guild.help.package_description(gf, [("ref-1", "foobar")]))
    Models
    ######
    <BLANKLINE>
    expert
    ######
    <BLANKLINE>
    *Sample model*
    <BLANKLINE>
    Operations
    ==========
    <BLANKLINE>
    evaluate
    ^^^^^^^^
    <BLANKLINE>
    train
    ^^^^^
    <BLANKLINE>
    Model flags
    ===========
    <BLANKLINE>
    **batch-size**
      *Number of images per batch (default is 100)*
    <BLANKLINE>
    **epochs**
      *Number of epochs to train (default is 5)*
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
      * (default is 50000)*
    <BLANKLINE>
    **epochs**
      * (default is 1)*
    <BLANKLINE>
    train
    ^^^^^
    <BLANKLINE>
    Model flags
    ===========
    <BLANKLINE>
    **batch-size**
      *Number of images per batch (default is 100)*
    <BLANKLINE>
    **epochs**
      *Number of epochs to train (default is 10)*
    <BLANKLINE>
    **learning-rate**
      *Learning rate for training (default is 0.001)*
    <BLANKLINE>
    References
    ##########
    <BLANKLINE>
    ref-1: foobar
    <BLANKLINE>
