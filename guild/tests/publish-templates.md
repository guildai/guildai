# Publish Templates

Templates are used to generate a published run. Template consist of
rendered files and supporting files. A published run is first copied
to its destination. Next the template is used to generate rendered
files that are written to the destination.

Publish support is provided by `guild.publish`.

    >>> from guild import publish

## Simple template

Here's a simple template:

    >>> simple = sample("templates/simple")

    >>> dir(simple)
    ['README.md',
     '_footer.md',
     '_footer_header.html',
     '_header.md',
     'a',
     'b',
     'hello.png']

Files starting with "_" are supporting files that are included by
templates and are not written when the template is generated.

Let's create a template:

    >>> pt = publish.Template(simple)

The template generates these files:

    >>> pt.files
    ['README.md', 'a/A.md', 'b/B.html', 'hello.png']

Note that files starting with "_" are not generated.

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

    >>> from guild import run as runlib
    >>> run = runlib.from_dir(sample("runs", "360192fdf9b74f2fad5f514e9f2fdadb"))

    >>> from guild import run_util
    >>> formatted = run_util.format_run(run)

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
    | Started     | ...     |
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
     '360192fdf9b74f2fad5f514e9f2fdadb/.guild/PENDING',
     '360192fdf9b74f2fad5f514e9f2fdadb/.guild/attrs/env',
     '360192fdf9b74f2fad5f514e9f2fdadb/.guild/attrs/started',
     '360192fdf9b74f2fad5f514e9f2fdadb/.guild/opref',
     '360192fdf9b74f2fad5f514e9f2fdadb/README.md']

    >>> cat(path(dest, "360192fdf9b74f2fad5f514e9f2fdadb/README.md")) # doctest: +REPORT_UDIFF
    [Published runs](../README.md)
    <BLANKLINE>
    # mnist:train
    <BLANKLINE>
    | ID                | Operation         | Started           | Duration           | Status           | Label           |
    | --                | ---------         | ---------         | --------           | ------           | -----           |
    | 360192fd | mnist:train | ... | &nbsp; | pending |  |
    <BLANKLINE>
    ## Flags
    <BLANKLINE>
    There are no flags for this run.
    <BLANKLINE>
    ## Scalars
    <BLANKLINE>
    There are no scalars for this run.
    <BLANKLINE>
    ## Files
    <BLANKLINE>
    There are no files for this run.
    <BLANKLINE>
    ## Images
    <BLANKLINE>
    There are no images for this run.
    <BLANKLINE>
    ## Source
    <BLANKLINE>
    There are no source files for this run.
    <BLANKLINE>
    ## Attributes
    <BLANKLINE>
    | Name        | Value                 |
    | -           | -                     |
    | ID          | 360192fdf9b74f2fad5f514e9f2fdadb          |
    | Model       | mnist       |
    | Operation   | train     |
    | Status      | pending      |
    | Marked      | no      |
    | Started     | ...     |
    | Stopped     |      |
    | Label       |        |
    | Exit Status |  |
    <BLANKLINE>
