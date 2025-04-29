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

The file is not yet part of a commit, so we still get `NoCommit` for the
subdir.

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

If Git meets the ls-files target (i.e. is at least version 2.32.0), the
check `error` is None.

    >>> print(check_result.error, check_result.out)  # doctest: +GIT_LS_FILES_TARGET
    None ...

Otherwise, we expected to see the following error and output from the
check:

    >>> print(check_result.error, check_result.out)  # doctest: -GIT_LS_FILES_TARGET
    unexpected output for ls-files:
     b''

## Git executable

Guild uses the `PATH` environment variable to locate the Git executable.
However, it can also be specified in user config under the
`git.exeutable`.

For tests, we assume that Git is available on `PATH`.

    >>> from guild import util

    >>> util.which("git") is not None
    True

This is used to get the Git version.

    >>> gitver = vcs_util.git_version()

    >>> isinstance(gitver, tuple), gitver
    (True, ...)

    >>> all(type(x) is int for x in gitver), gitver
    (True, ...)

Guild caches read values from

If we specify an invalid path for the Git executable in user config,
Guild doesn't see it because it caches results from previous calls.

    >>> with UserConfig({"git": {"executable": "not-a-valid-git-exe"}}):
    ...     vcs_util.git_version()
    (..., ..., ...)

We need to reset `guild.vcs_util._git_exe`, which is the state
associated with the Git executable value.

    >>> def reset_git_exe_state():
    ...     vcs_util._git_exe._val = vcs_util._git_exe._unread

    >>> reset_git_exe_state()

    >>> with UserConfig({"git": {"executable": "not-a-valid-git-exe"}}):
    ...      vcs_util.git_version()
    Traceback (most recent call last):
    GitNotInstalled

Reset the state and try again.

    >>> reset_git_exe_state()

    >>> vcs_util.git_version()
    (..., ..., ...)

When used in the context of source code copying, Guild handles a missing
or invalid Git exe by logging a warning message when run for Git repos.

To illustrate, first create a project that is not a Git repo.

    >>> project_dir = mkdtemp()
    >>> touch(path(project_dir, "test.py"))

Guild uses the `git` executable to determine if a project is a Git repo.

    >>> vcs_util.git_project_select_rules(project_dir)
    Traceback (most recent call last):
    NoVCS: ('...', (128, ...not a git repository...))

When we initialize a Git repo in the project, we get select rules for
the project.

    >>> quiet("git init", cwd=project_dir)

    >>> vcs_util.git_project_select_rules(project_dir)
    [<guild.file_util.FileSelectRule object ...>,
     <guild.vcs_util._GitignoreSelectRule ...>,
     <guild.file_util.FileSelectRule ...>]

However, when we intentionally disable Git by using invalid
configuration, Guild is unable to process the project source code files.
In this case Guild prints a warning message.

We need to reset the Git exe state.

    >>> reset_git_exe_state()

Call `git_project_select_rules` using invalid configuration.

    >>> with LogCapture() as logs:
    ...     with UserConfig({"git": {"executable": "not-a-git-exe"}}):
    ...         vcs_util.git_project_select_rules(project_dir)
    Traceback (most recent call last):
    NoVCS: ...

    >>> logs.print_all()
    WARNING: The current project appears to use Git for version control
    but git is not available on the system path. To apply Git's source
    code rules to this run, install Git [1] or specify the Git executable
    in Guild user config [2].
    <BLANKLINE>
    [1] https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
    [2] https://my.guildai.org/t/user-config-reference
    <BLANKLINE>
    To disable this warning, set 'NO_WARN_GIT_MISSING=1'

Guild does show the warning if the project is not a Git repo.

The invalid Git exe is cached so we don't need to run with user config.

    >>> vcs_util._git_exe._val
    'not-a-git-exe'

    >>> rmdir(path(project_dir, ".git"))
    >>> with LogCapture() as logs:
    ...    vcs_util.git_project_select_rules(project_dir)
    Traceback (most recent call last):
    NoVCS: ...

    >>> logs.print_all()

Reset the Git exe state.

    >>> reset_git_exe_state()
