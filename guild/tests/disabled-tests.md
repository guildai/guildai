# Disabled tests

The following tests have disabled tests (designated by lines starting
with " >> ").

    >>> def print_disabled_tests():
    ...     for path in findl("."):
    ...         if (
    ...             not path.endswith(".md") or
    ...             path.split(os.path.sep, 1)[0] == "samples"
    ...         ):
    ...             continue
    ...         for i, line in enumerate(open(path).readlines()):
    ...             if line.startswith("    >> "):
    ...                 print(f"# {path}:{i + 1}: {line.rstrip()}")

    >>> print_disabled_tests()  # doctest: +REPORT_UDIFF
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
    # run-impl.md:854:     >> run("guild run --restart down1 upstream=up1 -y")
    # uat/dvc.md:...
