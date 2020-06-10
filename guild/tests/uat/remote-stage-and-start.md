# Remote stage and restart

Delete remote runs as baseline.

    >>> quiet("guild runs rm -y -r guild-uat")

Stage hello example:

    >>> cd(example("hello-package"))
    >>> run("guild run -y hello msg='staged example' --stage -r guild-uat",
    ...     ignore="Refreshing")
    Building package
    ...
    Initializing remote run
    Copying package
    ...
    Installing package and its dependencies
    ...
    Installing collected packages: gpkg.hello
    Successfully installed gpkg.hello-0.1
    hello staged as on guild-uat as ...
    To start the operation, use 'guild run -r guild-uat --start ...'
    <exit 0>

Stage hello package from example dir:

    >>> run("guild run -y gpkg.hello/hello:from-flag "
    ...     "message='staged package from examples dir' "
    ...     "--stage -r guild-uat")
    Building package
    ...
    gpkg.hello/hello:from-flag staged as on guild-uat as ...
    To start the operation, use 'guild run -r guild-uat --start ...'
    <exit 0>

Stage hello package from an empty temp dir:

    >>> tmp = mkdtemp()
    >>> cd(tmp)
    >>> run("guild run -y hello:from-flag "
    ...     "message='staged package from empty dir' "
    ...     "--stage -r guild-uat")
    Building package
    ...
    gpkg.hello/hello:from-flag staged as on guild-uat as ...
    To start the operation, use 'guild run -r guild-uat --start ...'
    <exit 0>

Remote runs:

    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.hello/hello:from-flag  ...  staged  message='staged package from empty dir'
    [2:...]  gpkg.hello/hello:from-flag  ...  staged  message='staged package from examples dir'
    [3:...]  gpkg.hello/hello            ...  staged  msg='staged example'
    <exit 0>

Start latest staged run:

    >>> run("""
    ...   run_id=`guild runs info 1 -r guild-uat | grep ^id: | cut -d' ' -f2`;
    ...   guild run -y --start $run_id -r guild-uat
    ...   """)
    Getting remote run info
    Initializing remote run for restart
    Starting gpkg.hello/hello:from-flag on guild-uat as ...
    staged package from empty dir
    Run ... stopped with a status of 'completed'
    <exit 0>

    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.hello/hello:from-flag  ...  completed  message='staged package from empty dir'
    [2:...]  gpkg.hello/hello:from-flag  ...  staged     message='staged package from examples dir'
    [3:...]  gpkg.hello/hello            ...  staged     msg='staged example'
    <exit 0>

Start first staged run:

    >>> run("""
    ...   run_id=`guild runs info 3 -r guild-uat | grep ^id: | cut -d' ' -f2`;
    ...   guild run -y --start $run_id -r guild-uat
    ...   """)
    Getting remote run info
    Initializing remote run for restart
    Starting gpkg.hello/hello on guild-uat as ...
    staged example
    Run ... stopped with a status of 'completed'
    <exit 0>

    >>> run("guild runs -r guild-uat")
    [1:...]  gpkg.hello/hello            ...  completed  msg='staged example'
    [2:...]  gpkg.hello/hello:from-flag  ...  completed  message='staged package from empty dir'
    [3:...]  gpkg.hello/hello:from-flag  ...  staged     message='staged package from examples dir'
    <exit 0>
