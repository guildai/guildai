# Disabled tests

This test codifies the disabled tests under `guild/tests`.

Tests are disabled either using a `+FIXME` doctest option or by the
convention of changing the test prefix from `>>>` to `>>`.

Ideally there are no disabled tests in the suite but in some cases
it's necessary to move past a time consuming/low value fix. The list
below should be kept to a minimum and addressed by either fixing the
tests or deleting them from the suite.

## Helper functions

    >>> def iter_test_lines():
    ...     for path in findl("."):
    ...         if (
    ...             path == "disabled-tests.md" or
    ...             not path.endswith(".md") or
    ...             path.split(os.path.sep, 1)[0] == "samples"
    ...         ):
    ...             continue
    ...         for i, line in enumerate(open(path).readlines()):
    ...             yield i + 1, line.rstrip(), path

## Enuermate disabled tests

    >>> for lineno, line, path in iter_test_lines():
    ...     if line.startswith("    >> ") or "+FIXME" in line:
    ...         print(f"# {path}:{lineno}: {line}")  # doctest: +REPORT_UDIFF
    # breakpoints.md:2: doctest: +FIXME_CI  # Issue appears specific to CI env (can't reproduce over ssh - may be tty related)
    # imports.md:2: doctest: +FIXME_CI  # Spurious warnings from matplotlib (CI is directing stderr to stdout)
    # uat/evaluate-mnist-intro-example.md:2: doctest: +FIXME  # Example needs to be updated
    # uat/mnist-example-runs-after-intro-evaluate.md:2: doctest: +FIXME  # Dep on evaluate-mnist-intro-example.md
    # uat/r-basic.md:2: doctest: +FIXME -WINDOWS  # Need to clean this up for 0.9!!
    # uat/r-scripts.md:2: doctest: +R +FIXME_CI
    # uat/remote-azure-blob.md:2: doctest: +FIXME  # Need to reinstate test account with MS
    # uat/tensorflow2.md:6: doctest: +FIXME  # Shows our TF summary patching is broken
