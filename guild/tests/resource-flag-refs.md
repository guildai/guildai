# Resource flag refs

The tests below run code defined in the `resource-flag-refs` project.

    >>> use_project("resource-flag-refs")

Default resource resolution:

    >>> run("guild run op1", timeout=2)
    You are about to run op1
      filename: foo
    Continue? (Y/n)
    <exit -9>

    >>> run("guild run op1 -y")
    Resolving file

    >>> run("guild ls -n")
    foo-file.txt

Use flag to specify a file via a resource ref:

    >>> run("guild run op1 filename=bar", timeout=2)
    You are about to run op1
      filename: bar
    Continue? (Y/n)
    <exit -9>

    >>> run("guild run op1 filename=bar -y")
    Resolving file

    >>> run("guild ls -n")
    bar-file.txt

Flag that can't be resolved to a file:

    >>> run("guild run op1 filename=baz -y")
    Resolving file
    guild: run failed because a dependency was not met: could not resolve
    'file' in file resource: cannot find source file 'baz-file.txt'
    <exit 1>

Op with a reference to a missing flag:

    >>> run("guild run op2 -y")
    Resolving file
    guild: run failed because a dependency was not met: could not resolve 'file'
    in file resource: cannot resolve '${undefined}' in file: undefined reference 'undefined'
    <exit 1>

We can force the flag however.

    >>> run("guild run op2 undefined=foo-file.txt --force-flags -y")
    Resolving file

    >>> run("guild ls -n")
    foo-file.txt

The `op3` uses a flag ref in a rename.

    >>> run("guild run op3 -y")
    Resolving file:foo-file.txt

    >>> run("guild ls -n")
    baz.txt

Specifying the value for the renamed file.

    >>> run("guild run op3 name=bam -y")
    Resolving file:foo-file.txt

    >>> run("guild ls -n")
    bam.txt

`op4` and `op5` contain undefined flag ref in rename specs.

    >>> run("guild run op4 -y")
    Resolving file:foo-file.txt
    guild: run failed because a dependency was not met: error renaming
    source foo-file.txt ('foo-file.txt' -> '${undefined}'): resolution error:
    cannot resolve '${undefined}': undefined reference 'undefined'
    <exit 1>

    >>> run("guild run op5 -y")
    Resolving file:foo-file.txt
    guild: run failed because a dependency was not met: error renaming source
    foo-file.txt ('${undefined}' -> 'bar.txt'): resolution error: cannot resolve
    '${undefined}': undefined reference 'undefined'
    <exit 1>

`op6` exposes its required file source by specifying `flag-name`.

    >>> run("guild run op6", timeout=2)
    You are about to run op6
      file: foo-file.txt
    Continue? (Y/n)
    <exit -9>

We can specify an alternative file using this flag.

    >>> run("guild run op6 file=bar-file.txt -y")
    Resolving file
    Using bar-file.txt for file

    >>> run("guild ls -n")
    bar-file.txt

We cannot otherwise specify the value (e.g. by using default source
names).

    >>> run("guild run op6 file:foo-file.txt=bar-file.txt -y")
    guild: unsupported flag 'file:foo-file.txt'
    Try 'guild run op6 --help-op' for a list of flags or use
    --force-flags to skip this check.
    <exit 1>

    >>> run("guild run op6 foo-file.txt=bar-file.txt -y")
    guild: unsupported flag 'foo-file.txt'
    Try 'guild run op6 --help-op' for a list of flags or use
    --force-flags to skip this check.
    <exit 1>
