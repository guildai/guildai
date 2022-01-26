# DvC support

These tests make use of the `dvc` example. This project is used as a
template for a working DvC repo. We run `setup.py` to generate a
project we can work with.


    >>> tmp = mkdtemp()
    >>> cd(example("dvc"))
    >>> run("python setup.py '%s'" % tmp)
    Initializing ...
    Initializing Git
    Initializing DvC
    Copying source code files
    Creating first Git commit
    <exit 0>

    >>> cd(tmp)

    >>> run("guild ops")  # doctest: +REPORT_UDIFF
    eval-models   Stage 'eval-models' imported from dvc.yaml
    hello         Stage 'hello' imported from dvc.yaml
    prepare-data  Stage 'prepare-data' imported from dvc.yaml
    train-models  Stage 'train-models' imported from dvc.yaml
    <exit 0>
