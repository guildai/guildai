# Remote diffing

Verify that a whole-run diff exits without error:

    >>> quiet("guild diff --remote guild-uat -c 'diff -ur'")

Spot check various diffs (limit to legacy ops 'hello:from' pattern
match):

    >>> run("guild diff -Fo hello:from --flags -r guild-uat -c 'diff -ur'")
    --- ...
    +++ ...
    @@ -1 +1 @@
    -message: Howdy Guild!
    +file: msg.txt
    <exit 0>

    >>> run("guild diff -Fo hello:from -p output -r guild-uat -c 'diff -ur'")
    --- .../output ...
    +++ .../output ...
    @@ -1 +1,2 @@
    -Howdy Guild!
    +Hello Guild, from a required file!
    +
    <exit 0>

    >>> run("guild diff -Fo hello:from --output -r guild-uat -c 'diff -ur'")
    --- .../.guild/output ...
    +++ .../.guild/output ...
    @@ -1 +1,2 @@
    -Howdy Guild!
    +Hello Guild, from a required file!
    +
    <exit 0>
