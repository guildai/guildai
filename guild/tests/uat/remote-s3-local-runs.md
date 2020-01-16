# S3 local runs

Generate sample runs for S3 tests.

    >>> cd("examples/hello")

    >>> quiet("guild runs rm -y")

    >>> run("guild run -y from-flag message='hello run-1' --label run-1")
    hello run-1
    <exit 0>

    >>> run("guild run -y from-flag message='hello run-2' --label run-2")
    hello run-2
    <exit 0>
