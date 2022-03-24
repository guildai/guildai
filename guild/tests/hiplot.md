# HiPlot

Generate a run for HiPlot. We use the `noisy.py` script in the
`optimizers` project.

    >>> cd(sample("projects", "optimizers"))  # doctest: -PY2 -PY35
    >>> gh = mkdtemp()  # doctest: -PY2 -PY35
    >>> run("guild -H %s run noisy.py x=[0.1,0.2] -y" % gh)  # doctest: -PY2 -PY35
    ???INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=0.1)
    x: 0.100000
    noise: 0.1
    loss: ...
    INFO: [guild] Running trial ...: noisy.py (noise=0.1, x=0.2)
    x: 0.200000
    noise: 0.1
    loss: ...
    <exit 0>

Our runs:

    >>> run("guild -H %s runs" % gh)  # doctest: -PY2 -PY35
    [1:...]  noisy.py   ...  completed  noise=0.1 x=0.2
    [2:...]  noisy.py   ...  completed  noise=0.1 x=0.1
    <exit 0>

Generate an HTML page for comparison using hiplot tool:

    >>> tmp = mkdtemp()  # doctest: -PY2 -PY35
    >>> html = path(tmp, "compare.html")  # doctest: -PY2 -PY35
    >>> run("guild -H %s compare --tool hiplot" % gh, env={"HIPLOT_HTML": html})  # doctest: -PY2 -PY35
    Preparing data for compare
    Saved HiPlot HTML to .../compare.html
    <exit 0>

Show some bytes to sanity-check the file:

    >>> open(html, "r").read(60)  # doctest: -PY2 -PY35 -NORMALIZE_PATHS
    '<!DOCTYPE html>\n\n<html>\n<head>\n<meta content="text/html;char'
