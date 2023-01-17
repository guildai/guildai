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
    # dependencies.md:812:     >> resolve(simple_config, run)
    # ls-cmd-2.md:174:     >> run("guild ls -p .guild --sourcecode -n")
    # uat/concurrent-queues.md:4: doctest: +FIXME
    # uat/dask-scheduler-resources.md:4: doctest: +FIXME
    # uat/dask-scheduler.md:4: doctest: +FIXME
    # uat/dependencies.md:5: doctest: +FIXME
    # uat/dvc.md:4: doctest: +FIXME
    # uat/dvc.md:384:     >> run("guild run train-models-dvc-stage -y")  # doctest: +REPORT_UDIFF
    # uat/dvc.md:400:     >> run("guild ls -n")  # doctest: +REPORT_UDIFF
    # uat/dvc.md:415:     >> run("guild run eval-models-dvc-stage -y")  # doctest: +REPORT_UDIFF
    # uat/dvc.md:433:     >> run("guild ls -n")  # doctest: +REPORT_UDIFF
    # uat/dvc.md:456:     >> run("guild cat -p dvc.yaml")
    # uat/dvc.md:467:     >> run("guild ls -np models-eval.json")
    # uat/dvc.md:473:     >> run("guild runs info")
    # uat/dvc.md:490:     >> run("guild run train-models-dvc-dep train.C=2.0 -y")
    # uat/dvc.md:508:     >> run("guild run faketrain-dvc-stage x=[-1.0,0.0,1.0] -y")  # doctest: +REPORT_UDIFF
    # uat/dvc.md:535:     >> run("guild compare -t -cc .operation,.status,.label,=noise,=x,loss -n3")
    # uat/dvc.md:555:     >> quiet("guild runs rm -y")
    # uat/dvc.md:560:     >> run("guild run train-models-dvc-stage -y")
    # uat/dvc.md:570:     >> run("guild run prepare-data-dvc-dep -y")
    # uat/dvc.md:581:     >> run("guild runs info")
    # uat/dvc.md:591:     >> run("guild run train-models-dvc-stage -y")
    # uat/dvc.md:614:     >> run("guild run dvc.yaml:faketrain --help-op")
    # uat/dvc.md:629:     >> run("guild run dvc.yaml:faketrain x=[0.2,0.3] -y")  # doctest: +REPORT_UDIFF
    # uat/dvc.md:651:     >> run("guild runs info")
    # uat/dvc.md:672:     >> quiet("guild runs rm -py")
    # uat/dvc.md:676:     >> run("guild run dvc.yaml:train-models -y")
    # uat/dvc.md:687:     >> run("guild run dvc.yaml:prepare-data -y")
    # uat/dvc.md:700:     >> run("guild run dvc.yaml:train-models -y")
    # uat/evaluate-mnist-intro-example.md:2: doctest: +FIXME  # Example needs to be updated
    # uat/mnist-example-runs-after-intro-evaluate.md:2: doctest: +FIXME  # Dep on evaluate-mnist-intro-example.md
    # uat/project-sourcecode.md:4: doctest: +FIXME
    # uat/r-basic.md:143:     >> from guild.plugins.r_script import op_data_for_script
    # uat/r-basic.md:148:     >> def op_data(script):
    # uat/r-basic.md:157:     >> op_data("empty.R")
    # uat/r-basic.md:165:     >> op_data("simple.R")
    # uat/r-basic.md:178:     >> run("guild run simple.R -y")
    # uat/remote-azure-blob.md:2: doctest: +FIXME
    # uat/remote-deps.md:4: doctest: +FIXME
    # uat/required-operation.md:5: doctest: +FIXME
    # uat/stage-deps.md:4: doctest: +FIXME
    # uat/tensorflow2.md:6: doctest: +FIXME
    # uat/test-flags.md:2: doctest: +FIXME  # Old TF tests - update with current API
