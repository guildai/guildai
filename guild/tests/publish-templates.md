# Publish Templates

    >>> from guild import publish

## Simple Example

Load a simple example:

    >>> pt = publish.Template(sample("templates/simple"))

The template generates these files:

    >>> pt.files
    ['README.md', 'a/A.md', 'b/B.html', 'hello.png']

Let's create a directory to contain the generated files:

    >>> dest = mkdtemp()

And generate the files:

    >>> pt.generate(dest, {"a_msg": "whoop"})

The generated files:

    >>> find(dest)
    ['README.md', 'a/A.md', 'b/B.html', 'hello.png']

README.md:

    >>> cat(path(dest, "README.md")) # doctest: +REPORT_UDIFF
    # Report
    <BLANKLINE>
    This is a fancy report!
    <BLANKLINE>
    Hello: ![](hello.png)
    <BLANKLINE>
    [a](a/A.md)
    <BLANKLINE>
    [b](b/B.html)
    <BLANKLINE>
    <hr>
    <BLANKLINE>
    The end.

a/A.md:

    >>> cat(path(dest, "a/A.md"))
    This is A!
    <BLANKLINE>
    A footer says: whoop

b/B.html:

    >>> cat(path(dest, "b/B.html"))
    <p>This is B!</p>

## Sample Run Report

Load a run report:

    >>> pt = publish.Template(sample("templates/run-report"))

Format a run for the report:

    >>> run = guild.Run(sample("runs", "360192fdf9b74f2fad5f514e9f2fdadb"))
    >>> formatted = guild.format_run(run)

Target directory;

    >>> dest = mkdtemp()

Generate files:

    >>> pt.generate(dest, {"run": formatted})

The generated files:

    >>> find(dest)
    ['README.md']

README.md:

    >>> cat(path(dest, "README.md")) # doctest: +REPORT_UDIFF
    # Run Report
    <BLANKLINE>
    ## Attributes
    <BLANKLINE>
    | Attribute   | Value                 |
    | ---------   | -----                 |
    | ID          | 360192fdf9b74f2fad5f514e9f2fdadb          |
    | Directory   |          |
    | Model       | mnist       |
    | Operation   | mnist:train   |
    | Package     |          |
    | Status      | pending      |
    | Marked      | no      |
    | Started     | 2017-09-30 11:53:05     |
    | Stopped     |      |
    | Command     |      |
    | Exit Status |  |
    <BLANKLINE>
    ## Environment
    <BLANKLINE>
    ```BAR: abc
    FOO: 123```

## Default Run Template

The publish command uses `guild.publish` facilities as show above, but
provides a default template to render runs.

Here's a new dest dir:

    >>> dest = mkdtemp()

    >>> publish.publish_run(run, dest)

    >>> find(dest)
    ['.guild-archive',
     'mnist-train-2017_09_30-11_53_05-360192fd/.guild/PENDING',
     'mnist-train-2017_09_30-11_53_05-360192fd/.guild/attrs/env',
     'mnist-train-2017_09_30-11_53_05-360192fd/.guild/attrs/id',
     'mnist-train-2017_09_30-11_53_05-360192fd/.guild/attrs/started',
     'mnist-train-2017_09_30-11_53_05-360192fd/.guild/opref',
     'mnist-train-2017_09_30-11_53_05-360192fd/README.md']

    >>> cat(path(dest, "mnist-train-2017_09_30-11_53_05-360192fd/README.md"))
    # mnist:train
    <BLANKLINE>
    2017-09-30 11:53:05
    <BLANKLINE>
    ## Attributes
    <BLANKLINE>
    | Name      | Value             |
    | -         | -                 |
    | ID        | 360192fdf9b74f2fad5f514e9f2fdadb      |
    | Model     | mnist   |
    | Operation | train |
    | Status    | pending  |
    | Marked    | no  |
    | Started   | 2017-09-30 11:53:05 |
    | Stopped   |  |
    <BLANKLINE>
    ## Process Info
    <BLANKLINE>
    | Name      | Value             |
    | -         | -                 |
    | Command     |      |
    | Exit Status |  |
    <BLANKLINE>
    ## Files
    <BLANKLINE>
    There are no files for this run.
    <BLANKLINE>
    ## Source
    <BLANKLINE>
    | File | Size | Modified |
    | ---- | ---- | -------- |
    <BLANKLINE>
