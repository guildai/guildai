# Remote hello

These tests run various hello operations remotely.

    >>> cd("examples/hello")

## default

    >>> run("guild run default -r guild-uat-ssh -y")
    Building package
    ...
    Initializing remote run
    Copying package
    ...
    Installing collected packages: hello
    Successfully installed hello-0.0.0
    Starting hello:default on guild-uat-ssh as ...
    Hello Guild!
    Run ... stopped with a status of 'completed'
    <exit 0>

## from-flag

    >>> run("guild run from-flag message='Howdy Guild!' -r guild-uat-ssh -y")
    Building package
    ...
    Initializing remote run
    Copying package
    ...
    Installing collected packages: hello
    Successfully installed hello-0.0.0
    Starting hello:from-flag on guild-uat-ssh as ...
    Howdy Guild!
    Run ... stopped with a status of 'completed'
    <exit 0>

## from-file

    >>> run("guild run from-file -r guild-uat-ssh -y")
    Building package
    ...
    Initializing remote run
    Copying package
    ...
    Installing collected packages: hello
    Successfully installed hello-0.0.0
    Starting hello:from-file on guild-uat-ssh as ...
    Resolving msg-file dependency
    Hello Guild, from a required file!
    <BLANKLINE>
    Run ... stopped with a status of 'completed'
    <exit 0>
