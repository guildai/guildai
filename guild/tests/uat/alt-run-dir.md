# Alternate run directory

By default Guild manages runs in a location under its home
directory. In some cases a user may want to generate a run in an
alternative directory. A common case for this is during development
when models are changed frequently and it's important to either not
clutter the list of runs with errors or it's simply more convenient to
develop with a single run directory.

Let's run a `hello` operation using a specific run directory.

    >>> tmp = mkdtemp()

    >>> run("NO_PIP_FREEZE=1 guild run hello:default --run-dir '%s' -y" % tmp)
    Run directory is '...' (results will not be visible to Guild)
    Hello Guild!
    <exit 0>

And the generated files:

    >>> run("cd '%s'; find . | sort" % tmp,
    ...     ignore=["__pycache__", "say.pyc"]) # doctest: +REPORT_UDIFF
    .
    ./.guild
    ./.guild/attrs
    ./.guild/attrs/cmd
    ./.guild/attrs/deps
    ./.guild/attrs/env
    ./.guild/attrs/exit_status
    ./.guild/attrs/flags
    ./.guild/attrs/host
    ./.guild/attrs/id
    ./.guild/attrs/initialized
    ./.guild/attrs/op
    ./.guild/attrs/platform
    ./.guild/attrs/random_seed
    ./.guild/attrs/run_params
    ./.guild/attrs/sourcecode_digest
    ./.guild/attrs/started
    ./.guild/attrs/stopped
    ./.guild/attrs/user
    ./.guild/attrs/user_flags
    ./.guild/opref
    ./.guild/output
    ./.guild/output.index
    ./.guild/sourcecode
    ./.guild/sourcecode/guild.yml
    ./.guild/sourcecode/msg.txt
    ./.guild/sourcecode/say.py
    ./output
    <exit 0>
