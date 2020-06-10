# Resource flag refs

The tests below run code defined in the `resource-flag-refs` project.

    >>> project = Project(sample("projects", "resource-flag-refs"))

Default resource resolution:

    >>> run = project.run("op1")
    Resolving file dependency

    >>> project.ls(run)
    ['foo-file.txt']

Use flag to specify a file via a resource ref:

    >>> run = project.run("op1", flags={"filename": "bar"})
    Resolving file dependency

    >>> project.ls(run)
    ['bar-file.txt']

Flag that can't be resolved to a file:

    >>> run = project.run("op1", flags={"filename": "baz"})
    Resolving file dependency
    guild: run failed because a dependency was not met: could not resolve
    'file:baz-file.txt' in file resource: cannot find source file
    'baz-file.txt'
    <exit 1>

Op with a reference to a missing flag:

    >>> project.run("op2")
    guild: invalid definition for operation 'op2': invalid flag reference
    'file' in dependency 'undefined'
    <exit 1>

We can force the flag however.

    >>> run = project.run("op2",
    ...                   flags={"undefined": "foo-file.txt"},
    ...                   force_flags=True)
    Resolving file dependency

    >>> project.ls(run)
    ['foo-file.txt']

The `op3` uses a flag ref in a rename.

    >>> run = project.run("op3")
    Resolving file:foo-file.txt dependency

    >>> project.ls(run)
    ['baz.txt']

Specifying the value for the renamed file.

    >>> run = project.run("op3", flags={"name": "bam"})
    Resolving file:foo-file.txt dependency

    >>> project.ls(run)
    ['bam.txt']

`op4` and `op5` contain undefined flag ref in rename specs.

    >>> project.run("op4")
    guild: invalid definition for operation 'op4': invalid flag
    reference 'file:foo-file.txt' in dependency 'undefined'
    <exit 1>

    >>> project.run("op5")
    guild: invalid definition for operation 'op5': invalid flag
    reference 'file:foo-file.txt' in dependency 'undefined'
    <exit 1>
