# VCS Utils

    >>> from guild import vcs_util

## Git

Create a repo:

    >>> repo = mkdtemp()
    >>> cd(repo)

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

Init repo:

    >>> run("git init")
    Initialized empty Git repository in ...
    <exit 0>

    >>> dir()
    ['.git']

Initially the repo doesn't have any commits:

    >>> vcs_util.commit_for_dir(repo)
    Traceback (most recent call last):
    NoCommit: ...

Add a new file and commit:

    >>> touch("hello")
    >>> dir()
    ['.git', 'hello']

    >>> quiet("git add .")
    >>> quiet("git commit -m 'first commit'")
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

    >>> touch("hello-2")

And get the commit:

    >>> commit2, status2 = vcs_util.commit_for_dir(repo)

The change has not been committed, so the commit is the same:

    >>> commit2 == commit
    True

However, the working directory status is now flagged as changed:

    >>> status2
    True

Let's commit again:

    >>> quiet("git add .")
    >>> quiet("git commit -m 'second commit'")
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
    >>> cd(subdir)

    >>> vcs_util.commit_for_dir(subdir)
    Traceback (most recent call last):
    NoCommit: .../subdir

Let's add a file to the subdirectory.

    >>> touch("hello-3")

The file is not yet part of a commit, so we still get `NoCommit` for
the subdir.

    >>> vcs_util.commit_for_dir(subdir)
    Traceback (most recent call last):
    NoCommit: .../subdir

Let's add the subdir file and commit.

    >>> quiet("git add .")
    >>> quiet("git commit -m 'third commit'")
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

## Environment checks

`check_git_ls_files()` checks the behavior of Git with respect to its
listing of ignored files with the `--directory` option. Guild takes
advantage of an optimization in Git 2.32.0 and later, which lists
directories that can be safely ignored when those directories are not
explicitly listed in the `gitignore` spec. These directories can be
listed because all of their files are ignored via other `gitignore`
specs.

    >>> git_version = vcs_util.git_version()
    >>> check_result = vcs_util.check_git_ls_files()

If Git meets the ls-files target (i.e. is at least version 2.32.0),
the check `error` is None.

    >>> print(check_result.error, check_result.out)  # doctest: +GIT_LS_FILES_TARGET
    None ...

Otherwise, we expected to see the following error and output from the
check:

    >>> print(check_result.error, check_result.out)  # doctest: -GIT_LS_FILES_TARGET
    unexpected output for ls-files:
     b''
