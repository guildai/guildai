# ls cmd continued

These tests use the `ls-2` project.

    >>> use_project("ls-2")

    >>> run("guild ops")  # doctest: +REPORT_UDIFF
    op
    op-2
    op-legacy-sourcecode-dest

Run `op`.

    >>> run("guild run op -y")
    Resolving dependencies
    dep-1 says: hello
    dep-2 says: hola
    Generating files

Show run files.

Default:

    >>> run("guild ls -n")  # doctest: +REPORT_UDIFF
    dep-1.txt
    dep-2.txt
    generated-1.txt
    generated-2.txt
    guild.yml
    op.py
    subdir/
    subdir/generated-3.txt

All:

    >>> run("guild ls -n --all")  # doctest: +REPORT_UDIFF
    .guild/
    .guild/attrs/
    .guild/attrs/cmd
    .guild/attrs/deps
    .guild/attrs/env
    .guild/attrs/exit_status
    .guild/attrs/flags
    .guild/attrs/host
    .guild/attrs/id
    .guild/attrs/initialized
    .guild/attrs/op
    .guild/attrs/platform
    .guild/attrs/plugins
    .guild/attrs/random_seed
    .guild/attrs/run_params
    .guild/attrs/sourcecode_digest
    .guild/attrs/started
    .guild/attrs/stopped
    .guild/attrs/user
    .guild/attrs/user_flags
    .guild/manifest
    .guild/opref
    .guild/output
    .guild/output.index
    .hidden/
    .hidden/generated-4.txt
    .hidden/generated-5.txt
    dep-1.txt
    dep-2.txt
    generated-1.txt
    generated-2.txt
    guild.yml
    op.py
    subdir/
    subdir/generated-3.txt

Source code:

    >>> run("guild ls -n --sourcecode")
    guild.yml
    op.py

Dependencies:

    >>> run("guild ls -n --dependencies")
    dep-1.txt
    dep-2.txt

Generated:

    >>> run("guild ls -n --generated")
    .hidden/generated-4.txt
    .hidden/generated-5.txt
    generated-1.txt
    generated-2.txt
    subdir/generated-3.txt

`op-2` resolves a dependency with a symbolic link,

    >>> run("guild run op-2 -y")
    Resolving file:link-target
    Resolving file:dep-1.txt
    dep-1 says: hello
    dep-2 says: hola
    Generating files

    >>> run("guild ls -n")  # doctest: -WINDOWS
    dep-1.txt
    dep-2.txt
    generated-1.txt
    generated-2.txt
    guild.yml
    linked/
    op.py
    subdir/
    subdir/generated-3.txt

Windows does not play well with symbolic links and Guild's behavior on
Windows is incorrect. It's documented here.

`linked`, which is a linked directory, is considered a file on Windows
and is listed without a trailing slash.

    >>> run("guild ls -n")  # doctest: +WINDOWS_ONLY
    dep-1.txt
    dep-2.txt
    generated-1.txt
    generated-2.txt
    guild.yml
    linked
    op.py
    subdir/
    subdir/generated-3.txt
    
Show dependencies.

    >>> run("guild ls -n -d")  # doctest: -WINDOWS
    dep-1.txt
    linked/

    >>> run("guild ls -n -d")  # doctest: +WINDOWS_ONLY
    dep-1.txt
    linked

Guild doesn't list under `linked` by default. We need the
`--follow-links` option.

    >>> run("guild ls -ndL")  # doctest: -WINDOWS
    dep-1.txt
    linked/
    linked/file-1
    linked/file-2
    linked/subdir/file-3

The behavior under Windows is particularly egregious as links cannot
be traversed (the underlying support in Python via `os.walk` does not
traverse these files on Windows).

    >>> run("guild ls -ndL")  # doctest: +WINDOWS_ONLY
    dep-1.txt
    linked

`op-legacy-sourcecode-dest` copies sourcecode to `.guild/sourcecode`.

    >>> run("guild run op-legacy-sourcecode-dest -y")
    Resolving dependencies
    dep-1 says: hello
    dep-2 says: hola
    Generating files

    >>> run("guild ls -n")
    dep-1.txt
    dep-2.txt
    generated-1.txt
    generated-2.txt
    subdir/
    subdir/generated-3.txt

Source code files are located under `.guild/sourcecode`.

    >>> run("guild ls -n -p .guild/sourcecode")
    .guild/sourcecode/
    .guild/sourcecode/guild.yml
    .guild/sourcecode/op.py

We can list source code file using `--sourcecode`. Source code files
are shown by default even when located in hidden directories.

    >>> run("guild ls --sourcecode -n")
    .guild/sourcecode/guild.yml
    .guild/sourcecode/op.py

    >>> run("guild ls -p .guild --sourcecode -n")
    .guild/sourcecode/guild.yml
    .guild/sourcecode/op.py

    >>> run("guild ls -p .guild/sourcecode --sourcecode -n")
    .guild/sourcecode/guild.yml
    .guild/sourcecode/op.py
