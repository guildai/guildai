# Remote hello

These tests run various hello operations remotely.

    >>> cd(example("hello-package-legacy"))

## default

    >>> run("guild run default -r guild-uat -l h1 -y")
    Building package
    ...
    Initializing remote run
    Copying package
    ...
    Installing collected packages: hello
    Successfully installed hello-0.0.0
    Starting hello:default on guild-uat as ...
    Hello Guild!
    Run ... stopped with a status of 'completed'
    <exit 0>

## from-flag

    >>> run("guild run from-flag message='Howdy Guild!' -r guild-uat -y")
    Building package
    ...
    Initializing remote run
    Copying package
    ...
    Installing collected packages: hello
    Successfully installed hello-0.0.0
    Starting hello:from-flag on guild-uat as ...
    Howdy Guild!
    Run ... stopped with a status of 'completed'
    <exit 0>

## from-file

    >>> run("guild run from-file -r guild-uat -t h2 -y")
    Building package
    ...
    Initializing remote run
    Copying package
    ...
    Installing collected packages: hello
    Successfully installed hello-0.0.0
    Starting hello:from-file on guild-uat as ...
    Hello Guild, from a required file!
    <BLANKLINE>
    Run ... stopped with a status of 'completed'
    <exit 0>

List runs using various filter on remote.

    >>> run("guild runs --filter operation=hello/hello:default -r guild-uat")
    [1:...]  hello/hello:default  ...  completed  h1
    <exit 0>

    >>> run("guild runs --filter 'op contains from' -r guild-uat")
    [1:...]  hello/hello:from-file  ...  completed  h2 file=msg.txt
    [2:...]  hello/hello:from-flag  ...  completed  message='Howdy Guild!'
    <exit 0>

    >>> run("guild runs --filter 'label contains howdy' -r guild-uat")
    [1:...]  hello/hello:from-flag  ...  completed  message='Howdy Guild!'
    <exit 0>
