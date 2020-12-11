# Model help

Model help support is provided by `guild.help`.

    >>> import guild.help

It's used to format help for a guildfile.

    >>> gf = guildfile.for_dir(sample("projects/mnist-pkg"))

## Package description

The `package_description` function returns a restructured text
formatted string.

    >>> print(guild.help.package_description(gf)) # doctest: +REPORT_UDIFF -NORMALIZE_WHITESPACE
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
    **batch-size**
      *Number of images per train batch (default is 100)*
    <BLANKLINE>
    **clones**
      *Number of clones to deploy to (default is calculated)
    <BLANKLINE>
      Choices:  calculate, 1, 2, 5
      *
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
    **batch-size**
      *Number of images per train batch (default is 100)*
    <BLANKLINE>
    **clones**
      *Number of clones to deploy to (default is calculated)
    <BLANKLINE>
      Choices:  calculate, 1, 2, 5
      *
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

## Markdown

Guild supports Markdown rendering via `guildfile_markdown_help`.

    >>> print(guild.help.guildfile_markdown_help(gf)) # doctest: +REPORT_UDIFF -NORMALIZE_WHITESPACE
    ## Overview
    <BLANKLINE>
    Guild AI supported models and operations are listed below. To run an
    operation, you must first install Guild AI by running:
    <BLANKLINE>
    ``` $ pip install guildai ```
    <BLANKLINE>
    Refer to [Install Guild AI](https://guild.ai/install) for detailed
    instructions.
    <BLANKLINE>
    To run a model operation use:
    <BLANKLINE>
    ``` $ guild run [MODEL:]OPERATION ```
    <BLANKLINE>
    `MODEL` is one of the model names listed below and `OPERATION` is an
    associated model operation or base operation.
    <BLANKLINE>
    You may set operation flags using `FLAG=VALUE` arguments to the run command.
    Refer to the operations below for a list of supported flags.
    <BLANKLINE>
    For additional help using Guild, see [Guild AI
    Documentation](https://guild.ai/docs).
    <BLANKLINE>
    ## Models
    <BLANKLINE>
    ### expert
    <BLANKLINE>
    *Expert model*
    <BLANKLINE>
    #### Operations
    <BLANKLINE>
    ##### evaluate
    ###### Flags
    <dl>
    <dt>batch-size</dt>
    <dd>Number of images per eval batch (default is 50000)</dd>
    <dt>epochs</dt>
    <dd>Epochs to evaluate (default is 1)</dd>
    </dl>
    <BLANKLINE>
    ##### train
    ###### Flags
    <dl>
    <dt>batch-size</dt>
    <dd>Number of images per train batch (default is 100)</dd>
    <dt>clones</dt>
    <dd>Number of clones to deploy to (default is calculated)
    <BLANKLINE>
    Choices:  calculate, 1, 2, 5
    </dd>
    <dt>epochs</dt>
    <dd>Number of epochs to train (default is 5)</dd>
    <dt>learning-rate</dt>
    <dd>Learning rate for training (default is 0.001)</dd>
    </dl>
    <BLANKLINE>
    <BLANKLINE>
    ### intro
    <BLANKLINE>
    #### Operations
    <BLANKLINE>
    ##### evaluate
    ###### Flags
    <dl>
    <dt>batch-size</dt>
    <dd>Number of images per eval batch (default is 50000)</dd>
    <dt>epochs</dt>
    <dd>Epochs to evaluate (default is 2)</dd>
    </dl>
    <BLANKLINE>
    ##### train
    ###### Flags
    <dl>
    <dt>batch-size</dt>
    <dd>Number of images per train batch (default is 100)</dd>
    <dt>clones</dt>
    <dd>Number of clones to deploy to (default is calculated)
    <BLANKLINE>
    Choices:  calculate, 1, 2, 5
    </dd>
    <dt>epochs</dt>
    <dd>Number of epochs to train (default is 10)</dd>
    <dt>learning-rate</dt>
    <dd>Learning rate for training (default is 0.001)</dd>
    </dl>
    <BLANKLINE>
    #### References
    <BLANKLINE>
    - https://www.tensorflow.org/tutorials/layers
    <BLANKLINE>

## Console Help

Guild supports console help rendering via `guildfile_console_help`.

    >>> console_help = guild.help.guildfile_console_help(gf)

We strip ansi formatting for test output.

    >>> from guild import util
    >>> print(util.strip_ansi_format(console_help))  # doctest: +REPORT_UDIFF -NORMALIZE_WHITESPACE
    OVERVIEW
    <BLANKLINE>
        You are viewing help for operations defined in './samples/projects
        /mnist-pkg'.
    <BLANKLINE>
        To run an operation use 'guild run OPERATION' where OPERATION is one
        of options listed below. If an operation is associated with a model,
        include the model name as MODEL:OPERATION.
    <BLANKLINE>
        To list available operations, run 'guild operations'.
    <BLANKLINE>
        Set operation flags using 'FLAG=VALUE' arguments to the run command.
        Refer to the operations below for a list of supported flags.
    <BLANKLINE>
        For more information on running operations, try 'guild run --help'.
        For general information, try 'guild --help'.
    <BLANKLINE>
    MODELS
    <BLANKLINE>
        expert
    <BLANKLINE>
          Expert model
    <BLANKLINE>
          Operations:
    <BLANKLINE>
            evaluate
              Flags:
                batch-size  Number of images per eval batch (default is 50000)
                epochs      Epochs to evaluate (default is 1)
    <BLANKLINE>
            train
              Flags:
                batch-size     Number of images per train batch (default is 100)
                clones         Number of clones to deploy to (default is calculated)
    <BLANKLINE>
                               Choices:  calculate, 1, 2, 5
    <BLANKLINE>
                epochs         Number of epochs to train (default is 5)
                learning-rate  Learning rate for training (default is 0.001)
    <BLANKLINE>
    <BLANKLINE>
        intro
    <BLANKLINE>
          Operations:
    <BLANKLINE>
            evaluate
              Flags:
                batch-size  Number of images per eval batch (default is 50000)
                epochs      Epochs to evaluate (default is 2)
    <BLANKLINE>
            train
              Flags:
                batch-size     Number of images per train batch (default is 100)
                clones         Number of clones to deploy to (default is calculated)
    <BLANKLINE>
                               Choices:  calculate, 1, 2, 5
    <BLANKLINE>
                epochs         Number of epochs to train (default is 10)
                learning-rate  Learning rate for training (default is 0.001)
    <BLANKLINE>
          References:
    <BLANKLINE>
            - https://www.tensorflow.org/tutorials/layers
    <BLANKLINE>
