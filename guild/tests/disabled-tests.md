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
    # multi-run-deps.md:5:     >> cd(sample("projects", "multi-run"))
    # multi-run-deps.md:6:     >> set_guild_home(mkdtemp())
    # multi-run-deps.md:8:     >> run("guild run up x=1 --run-id=1 -y")
    # multi-run-deps.md:9:     >> run("guild run up x=2 --run-id=2 -y")
    # multi-run-deps.md:10:     >> run("guild run up x=3 --run-id=3 -y")
    # multi-run-deps.md:11:     >> run("guild run down --run-id=4 -y")
    # multi-run-deps.md:12:     >> run("guild run down up=1 --run-id=5 -y")
    # multi-run-deps.md:13:     >> run("guild run down up=1,3 --run-id=6 -y")
    # multi-run-deps.md:14:     >> run("guild run down up='3 2' --run-id=7 -y")
    # multi-run-deps.md:15:     >> run("guild runs")
    # r-script.md:2: doctest: +FIXME
    # uat/concurrent-queues.md:4: doctest: +FIXME
    # uat/dask-scheduler-resources.md:4: doctest: +FIXME
    # uat/dask-scheduler.md:4: doctest: +FIXME
    # uat/dependencies.md:5: doctest: +FIXME
    # uat/dvc.md:4: doctest: +FIXME
    # uat/dvc.md:405:     >> run("guild run train-models-dvc-stage -y")  # doctest: +REPORT_UDIFF
    # uat/dvc.md:421:     >> run("guild ls -n")  # doctest: +REPORT_UDIFF
    # uat/dvc.md:436:     >> run("guild run eval-models-dvc-stage -y")  # doctest: +REPORT_UDIFF
    # uat/dvc.md:454:     >> run("guild ls -n")  # doctest: +REPORT_UDIFF
    # uat/dvc.md:477:     >> run("guild cat -p dvc.yaml")
    # uat/dvc.md:488:     >> run("guild ls -np models-eval.json")
    # uat/dvc.md:494:     >> run("guild runs info")
    # uat/dvc.md:511:     >> run("guild run train-models-dvc-dep train.C=2.0 -y")
    # uat/dvc.md:529:     >> run("guild run faketrain-dvc-stage x=[-1.0,0.0,1.0] -y")  # doctest: +REPORT_UDIFF
    # uat/dvc.md:556:     >> run("guild compare -t -cc .operation,.status,.label,=noise,=x,loss -n3")
    # uat/dvc.md:576:     >> quiet("guild runs rm -y")
    # uat/dvc.md:581:     >> run("guild run train-models-dvc-stage -y")
    # uat/dvc.md:591:     >> run("guild run prepare-data-dvc-dep -y")
    # uat/dvc.md:602:     >> run("guild runs info")
    # uat/dvc.md:612:     >> run("guild run train-models-dvc-stage -y")
    # uat/dvc.md:635:     >> run("guild run dvc.yaml:faketrain --help-op")
    # uat/dvc.md:650:     >> run("guild run dvc.yaml:faketrain x=[0.2,0.3] -y")  # doctest: +REPORT_UDIFF
    # uat/dvc.md:672:     >> run("guild runs info")
    # uat/dvc.md:693:     >> quiet("guild runs rm -py")
    # uat/dvc.md:697:     >> run("guild run dvc.yaml:train-models -y")
    # uat/dvc.md:708:     >> run("guild run dvc.yaml:prepare-data -y")
    # uat/dvc.md:721:     >> run("guild run dvc.yaml:train-models -y")
    # uat/evaluate-mnist-intro-example.md:2: doctest: +FIXME  # Example needs to be updated
    # uat/mnist-example-runs-after-intro-evaluate.md:2: doctest: +FIXME  # Dep on evaluate-mnist-intro-example.md
    # uat/project-sourcecode.md:4: doctest: +FIXME
    # uat/remote-azure-blob.md:2: doctest: +FIXME
    # uat/remote-deps.md:4: doctest: +FIXME
    # uat/required-operation.md:5: doctest: +FIXME
    # uat/stage-deps.md:4: doctest: +FIXME
    # uat/tensorflow2.md:6: doctest: +FIXME
    # uat/test-flags.md:2: doctest: +FIXME  # Old TF tests - update with current API
