# Publishing Runs

The `runs publish` commands is used to publish runs. A published run
consists of:

- Copying runs to dest
- Generating a report using a template for each run
- Generating an index of runs

We'll use the `publish` sample project:

    >>> project = Project(sample("projects/publish"))

Generate a run to publish:

    >>> project.run("op")
    x: 3
    y: 1

    >>> run_id = project.list_runs()[0].id

## Extending default and redefining blocks (template `t1`)

Template `t1` extends `publish-default/README.md` and redefines each
block in the default template.

    >>> publish_dest = mkdtemp()

    >>> project.publish(template="t1", dest=publish_dest)
    Publishing [...] op ... ... completed
    Refreshing runs index

    >>> dir(path(publish_dest, run_id))
    ['.guild', 'README.md']

    >>> cat(path(publish_dest, run_id, "README.md"))
    Header
    <BLANKLINE>
    Title
    <BLANKLINE>
    Summary
    <BLANKLINE>
    Flags
    <BLANKLINE>
    Scalars
    <BLANKLINE>
    Files
    <BLANKLINE>
    Images
    <BLANKLINE>
    Source
    <BLANKLINE>
    Attributes
    <BLANKLINE>
    Footer

## New template with include (template `t2`)

Template `t2` replaces the default entirely but includes `_flags.md`.

    >>> publish_dest = mkdtemp()

    >>> project.publish(template="t2", dest=publish_dest)
    Publishing [...] op ... ... completed
    Refreshing runs index

    >>> dir(path(publish_dest, run_id))
    ['.guild', 'README.md', 'some_other_file.md']

    >>> cat(path(publish_dest, run_id, "README.md"))
    # Totally new report
    <BLANKLINE>
    Run: ...
    <BLANKLINE>
    | Name | Value |
    | ---- | ----- |
    | a | 1 |
    | b | 2 |

## Extend default with block def and redefined include (template `t3`)

Template `t3` extends default and defines header and footer blocks. It
also redefines the `_flags.md` include.

    >>> publish_dest = mkdtemp()

    >>> project.publish(template="t3", dest=publish_dest)
    Publishing [...] op ... ... completed
    Refreshing runs index

    >>> dir(path(publish_dest, run_id))
    ['.guild', 'README.md']

    >>> cat(path(publish_dest, run_id, "README.md"))
    Ze header
    <BLANKLINE>
    # op
    <BLANKLINE>
    | ID  | Operation | Started   | Duration | Status    | Label |
    | --  | --------- | --------- | -------- | ------    | ----- |
    | ... | op        | ... ...   | ...      | completed |       |
    <BLANKLINE>
    ## Flags
    <BLANKLINE>
    Redef of flags
    ## Scalars
    <BLANKLINE>
    | Key | Step | Value |
    | --- | ---- | ----- |
    | x   | 0    | 3.0   |
    | y   | 0    | 1.0   |
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
    | File                         | Size | Modified |
    | ----                         | ---- | -------- |
    | [op.py](.guild/source/op.py) | ...  | ...      |
    <BLANKLINE>
    ## Attributes
    <BLANKLINE>
    | Name        | Value     |
    | -           | -         |
    | ID          | ...       |
    | Model       |           |
    | Operation   | op        |
    | Status      | completed |
    | Marked      | no        |
    | Started     | ...       |
    | Stopped     | ...       |
    | Label       |           |
    | Exit Status | 0         |
    <BLANKLINE>
    Ze footer
