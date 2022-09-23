# HiPlot

Generate a run for HiPlot. We use the `noisy.py` script in the
`optimizers` project.

    >>> cd(sample("projects", "optimizers"))
    >>> gh = mkdtemp()
    >>> run("guild -H %s run noisy.py x=[0.1,0.2] -y" % gh)
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

    >>> run("guild -H %s runs" % gh)
    [1:...]  noisy.py   ...  completed  noise=0.1 x=0.2
    [2:...]  noisy.py   ...  completed  noise=0.1 x=0.1
    <exit 0>

Generate an HTML page for comparison using hiplot tool:

    >>> tmp = mkdtemp()
    >>> html = path(tmp, "compare.html")
    >>> run("guild -H %s compare --tool hiplot" % gh, env={"HIPLOT_HTML": html})
    Preparing data for compare
    Saved HiPlot HTML to .../compare.html
    <exit 0>

Show some bytes to sanity-check the file:

    >>> open(html, "r").read(60)  # doctest: -NORMALIZE_PATHS
    '<!DOCTYPE html>\n\n<html>\n<head>\n<meta content="text/html;char'
