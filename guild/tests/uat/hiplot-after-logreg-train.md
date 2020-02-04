# Compare using hiplot tool

Install `hiplot`:

    >>> quiet("pip install hiplot")

Confirm we have runs to compare:

    >>> run("guild runs")
    [1:...]  gpkg.mnist/logreg:train  ...  completed  batch-size=100 epochs=1 learning-rate=0.5
    <exit 0>

Generate an HTML page for comparison using hiplot tool:

    >>> tmp = mkdtemp()
    >>> html = path(tmp, "compare.html")

    >>> run("HIPLOT_HTML='%s' guild compare --tool hiplot" % html)
    Preparing data for compare
    Saved HiPlot HTML to .../compare.html
    <exit 0>

Show some bytes to sanity check the file:

    >>> open(html, "r").read(60)
    '<!DOCTYPE html>\n\n<html>\n<head>\n<meta content="text/html;char'
