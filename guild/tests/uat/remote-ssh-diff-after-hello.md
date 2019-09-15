# Remote diffing

Verify that a whole-run diff exits without error:

    >>> quiet("guild diff --remote guild-uat-ssh")

Spot check various diffs:

    >>> run("guild diff --flags -r guild-uat-ssh")
    --- ...
    +++ ...
    @@ -1 +1 @@
    -message: Howdy Guild!
    +file: msg.txt
    <exit 0>

    >>> run("guild diff -p output -r guild-uat-ssh")
    --- .../output ...
    +++ .../output ...
    @@ -1 +1,2 @@
    -Howdy Guild!
    +Hello Guild, from a required file!
    +
    <exit 0>

    >>> run("guild diff --output -r guild-uat-ssh")
    --- .../.guild/output ...
    +++ .../.guild/output ...
    @@ -1 +1,2 @@
    -Howdy Guild!
    +Hello Guild, from a required file!
    +
    <exit 0>
