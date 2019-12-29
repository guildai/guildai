# VCS Utils

    >>> from guild import vcs_util

Helper to run VCS commands:

    >>> import subprocess
    >>> from guild import util
    >>> def run(cmd, cwd):
    ...     subprocess.check_output(util.shlex_split(cmd), cwd=cwd)

## Git

Create a repo:

    >>> repo = mkdtemp()
    >>> run("git init", repo)

    >>> dir(repo)
    ['.git']

Configure user info to avoid errors on commit:

    >>> run("git config user.name test", repo)
    >>> run("git config user.email test@localhost", repo)

Initially the repo doesn't have any commits:

    >>> vcs_util.commit_for_dir(repo)
    Traceback (most recent call last):
    NoCommit: ...

Add a new file and commit:

    >>> touch(path(repo, "hello"))
    >>> dir(repo)
    ['.git', 'hello']

    >>> run("git add .", repo)
    >>> run("git commit -m 'first commit'", repo)
    >>> sleep(0.1)  # needed before reading commit log below

And get the commit:

    >>> commit, status = vcs_util.commit_for_dir(repo)

    >>> commit
    'git:...'

    >>> len(commit)
    44

The working directory is not changed:

    >>> status
    False

Let's modify the working directory:

    >>> touch(path(repo, "hello-2"))

And get the commit:

    >>> commit2, status2 = vcs_util.commit_for_dir(repo)

The change has not been committed, so the commit is the same:

    >>> commit2 == commit
    True

However, the working directory status is now flagged as changed:

    >>> status2
    True

Let's commit again:

    >>> run("git add .", repo)
    >>> run("git commit -m 'second commit'", repo)
    >>> sleep(0.1)

The latest commit:

    >>> commit3, status3 = vcs_util.commit_for_dir(repo)

    >>> commit3
    'git:...'

    >>> len(commit3)
    44

The commit has changed this time:

    >>> commit3 == commit
    False

And the working dir is unchanged:

    >>> status3
    False

A directory must be part of a repository commit history to get a commit.

    >>> subdir = path(repo, "subdir")
    >>> mkdir(subdir)

    >>> vcs_util.commit_for_dir(subdir)
    Traceback (most recent call last):
    NoCommit: .../subdir

Let's add a file to the subdirectory.

    >>> touch(path(subdir, "hello-3"))

The file is not yet part of a commit, so we still get `NoCommit` for
the subdir.

    >>> vcs_util.commit_for_dir(subdir)
    Traceback (most recent call last):
    NoCommit: .../subdir

Let's add the subdir file and commit.

    >>> run("git add .", subdir)
    >>> run("git commit -m 'third commit'", subdir)
    >>> sleep(0.1)

And the latest commit:

    >>> commit4, status4 = vcs_util.commit_for_dir(subdir)

    >>> commit4
    'git:...'

    >>> len(commit4)
    44

We have a new commit:

    >>> commit4 == commit3
    False

And our workspace is not change:

    >>> status4
    False

## Errors

An empty directory:

    >>> repo = mkdtemp()

    >>> vcs_util.commit_for_dir(repo)
    Traceback (most recent call last):
    NoCommit: ...

With an empty sentinel:

    >>> mkdir(path(repo, ".git"))
    >>> vcs_util.commit_for_dir(repo)
    Traceback (most recent call last):
    NoCommit: ...
