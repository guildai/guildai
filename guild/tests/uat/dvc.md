# DvC support

These tests make use of the `dvc` example.

This project is used as a template for a working DvC repo. We run
`setup.py` to generate a project we can work with.

    >>> tmp = mkdtemp()
    >>> cd(example("dvc"))
    >>> run("python setup.py '%s'" % tmp)
    Initializing ...
    Initializing Git
    Initializing DvC
    Copying source code files
    <exit 0>

    >>> cd(tmp)

    >> run("guild ops")  # doctest: +REPORT_UDIFF
    eval-models   Stage 'eval-models' imported from dvc.yaml
    hello         Stage 'hello' imported from dvc.yaml
    prepare-data  Stage 'prepare-data' imported from dvc.yaml
    train-models  Stage 'train-models' imported from dvc.yaml
    <exit 0>

## DvC resource sources

The dvc plugin adds support for a 'dvc' source type. This is used in
the sample project's 'hello-2' operation.

A dvc resource is resolved as a standard 'file' source if the file is
available.

We'll create a sample file in

    >>> run("guild run hello-2 -y")
    Resolving dvc:hello.in dependency
    Fetching DvC resource hello.in
    A       hello.in
    1 file added and 1 file fetched
    Hello World!
    <exit 0>
