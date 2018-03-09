# Delete sample run

Here are all our runs:

    >>> run("guild runs")
    [0:...]  ./sample-project/sample-project:train  ...  completed
    <exit 0>

Let's delete the sample run:

    >>> run("guild runs rm -o sample-project -y")
    Deleted 1 run(s)
    <exit 0>
