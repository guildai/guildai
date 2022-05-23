# VCS Source Code

    >>> from guild import vcs_util

## Git

Use a temp diretory for a Git repo.

    >>> repo = mkdtemp()
    >>> cd(repo)

Helper to print source files in repo.

    >>> def source(subdir=None):
    ...     dir = join_path(repo, subdir) if subdir else repo
    ...     for path in sorted(vcs_util.ls_files(dir)):
    ...         print(path)

Helper to print dir status.

    >>> def status(subdir=None, ignored=False):
    ...     dir = join_path(repo, subdir) if subdir else repo
    ...     status_files = vcs_util.status(dir, ignored=ignored)
    ...     for status in sorted(status_files, key=lambda s: s.path):
    ...          if status.status == "R":
    ...              print(f"{status.status}: {status.path} <- {status.renamed_from}")
    ...          else:
    ...              print(f"{status.status}: {status.path}")

An empty repo isn't supported.

    >>> source()
    Traceback (most recent call last):
    UnsupportedRepo: ...

    >>> status()
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

Files in an empty repo with no commit.

    >>> source()

    >>> status()

Add a file. This isn't tracked or ignored by Git.

    >>> touch("a")

    >>> source()
    a

    >>> status()
    ?: a

Add some more untracked, unignored files.

    >>> touch("b")
    >>> touch("c")

    >>> source()
    a
    b
    c

    >>> status()
    ?: a
    ?: b
    ?: c

Ignore a file.

    >>> write(".gitignore", "/a\n")

    >>> source()
    .gitignore
    b
    c

    >>> status()
    ?: .gitignore
    ?: b
    ?: c

    >>> status(ignored=True)
    ?: .gitignore
    !: a
    ?: b
    ?: c

Ignore another file.

    >>> write(".gitignore", "/c\n", append=True)

    >>> source()
    .gitignore
    b

    >>> status()
    ?: .gitignore
    ?: b

Add some more files.

    >>> mkdir("subdir")
    >>> touch("subdir/d")
    >>> touch("subdir/e")

    >>> source()
    .gitignore
    b
    subdir/d
    subdir/e

    >>> source("subdir")
    d
    e

    >>> status()
    ?: .gitignore
    ?: b
    ?: subdir/

    >>> status("subdir")
    ?: ./

Add all unignored files to index.

    >>> quiet("git add .")

    >>> source()
    .gitignore
    b
    subdir/d
    subdir/e

    >>> source("subdir")
    d
    e

    >>> status()
    A: .gitignore
    A: b
    A: subdir/d
    A: subdir/e

    >>> status("subdir")
    A: d
    A: e

Commit index changes.

    >>> quiet("git commit -m 'First commit'")

    >>> source()
    .gitignore
    b
    subdir/d
    subdir/e

    >>> status()

Delete a file. This does not change the file listing because the
deleted file is tracked by Git.

    >>> rm("subdir/e")

    >>> source()
    .gitignore
    b
    subdir/d
    subdir/e

    >>> status()
    D: subdir/e

Delete the file from git.

    >>> quiet("git add -u")

    >>> source()
    .gitignore
    b
    subdir/d

    >>> status()
    D: subdir/e

Commit the change.

    >>> quiet("git commit -m 'Delete subdir/e'")

    >>> source()
    .gitignore
    b
    subdir/d

    >>> status()

Checkout the previous commit.

    >>> quiet("git checkout HEAD^1")

    >>> source()
    .gitignore
    b
    subdir/d
    subdir/e

    >>> status()

Modify 'b' and 'subdir/e':

    >>> write("b", "xxx")
    >>> write("subdir/e", "yyy")

    >>> source()
    .gitignore
    b
    subdir/d
    subdir/e

    >>> status()
    M: b
    M: subdir/e

Rename 'subdir/d':

    >>> quiet("git mv subdir/d d")

    >>> source()
    .gitignore
    b
    d
    subdir/e

    >>> source("subdir")
    e

    >>> status()
    M: b
    R: d <- subdir/d
    M: subdir/e

    >>> status("subdir")
    D: d
    M: e

Show status including ignored files.

    >>> status(ignored=True)
    !: a
    M: b
    !: c
    R: d <- subdir/d
    M: subdir/e

    >>> status(ignored=False)
    M: b
    R: d <- subdir/d
    M: subdir/e
