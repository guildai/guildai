# Running a script on a remote

Guild doesn't support running scripts on a remote. The operation must
be defined in a Guild file.

    >>> cd("examples/hello")

    >>> run("guild run say.py -r guild-uat -y", ignore="Refreshing")
    Building package
    ...
    Initializing remote run
    Copying package
    ...
    Successfully installed hello-0.0.0
    Starting .../hello/say.py on guild-uat as ...
    Hello Guild!
    Run ... stopped with a status of 'completed'
    <exit 0>
