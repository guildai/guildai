# VCS Source Code

    >>> from guild import vcs_util

## Git

Use a temp diretory for a Git repo.

    >>> repo = mkdtemp()
    >>> cd(repo)

Helper to print source files in repo.

    >>> def source(subdir=None):
    ...     dir = join_path(repo, subdir) if subdir else repo
    ...     for path in sorted(vcs_util.iter_source_files(dir)):
    ...         print(path)

An empty repo isn't supported.

    >>> source()
    Traceback (most recent call last):
    UnsupportedRepo: ...

Pre-configure repo to suppress warning/error messages. We do this
manually before init to avoid init warnings.

    >>> mkdir(".git")
    >>> write(path(".git", "config"), """
    ... [core]
    ... repositoryformatversion = 0
    ... filemode = true
    ... bare = false
    ... logallrefupdates = true
    ... [user]
    ... name = test
    ... email = test@localhost
    ... [init]
    ... defaultBranch = master
    ... """)

Initialize a sample repo.

    >>> run("git init")
    Initialized empty Git repository in ...
    <exit 0>

Helper to print source files in repo.

    >>> def source(subdir=None):
    ...     dir = join_path(repo, subdir) if subdir else repo
    ...     for path in sorted(vcs_util.iter_source_files(dir)):
    ...         print(path)


Files in an empty repo with no commit.

    >>> source()

Add a file. This isn't tracked or ignored by Git.

    >>> touch("a")

    >>> source()
    a

Add some more untracked, unignored files.

    >>> touch("b")
    >>> touch("c")

    >>> source()
    a
    b
    c

Ignore a file.

    >>> write(".gitignore", "/a\n")

    >>> source()
    .gitignore
    b
    c

Ignore another file.

    >>> write(".gitignore", "/c\n", append=True)

    >>> source()
    .gitignore
    b

Add some more files.

    >>> mkdir("subdir")
    >>> touch("subdir/d")
    >>> touch("subdir/e")

    >>> source()
    .gitignore
    b
    subdir/d
    subdir/e

Add all unignored files to index.

    >>> quiet("git add .")

    >>> source()
    .gitignore
    b
    subdir/d
    subdir/e

Commit index changes.

    >>> quiet("git commit -m 'First commit'")

    >>> source()
    .gitignore
    b
    subdir/d
    subdir/e

Delete a file. This does not change the file listing because the
deleted file is tracked by Git.

    >>> rm("subdir/e")

    >>> source()
    .gitignore
    b
    subdir/d
    subdir/e

Delete the file from git.

    >>> quiet("git add -u")

    >>> source()
    .gitignore
    b
    subdir/d

Commit the change.

    >>> quiet("git commit -m 'Delete subdir/e'")

    >>> source()
    .gitignore
    b
    subdir/d

TODO:

- Checkout the previous commit and list source
