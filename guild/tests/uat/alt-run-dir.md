# Alternate run directory

By default Guild manages runs in a location under its home
directory. In some cases a user may want to generate a run in an
alternative directory. A common case for this is during development
when models are changed frequently and it's important to either not
clutter the list of runs with errors or it's simply more convenient to
develop with a single run directory.

Let's run a `hello` operation using a specific run directory.

    >>> run("guild run hello:default --run-dir hello-default -y")
    Run directory is '/.../hello-default' (results will not be visible to Guild)
    Hello Guild!
    <exit 0>

And the generated files:

    >>> run("find hello-default | sort",
    ...     ignore=["__pycache__", "say.pyc"]) # doctest: +REPORT_UDIFF
    hello-default
    hello-default/.guild
    hello-default/.guild/attrs
    hello-default/.guild/attrs/cmd
    hello-default/.guild/attrs/env
    hello-default/.guild/attrs/exit_status
    hello-default/.guild/attrs/flags
    hello-default/.guild/attrs/host
    hello-default/.guild/attrs/id
    hello-default/.guild/attrs/initialized
    hello-default/.guild/attrs/op
    hello-default/.guild/attrs/pip_freeze
    hello-default/.guild/attrs/platform
    hello-default/.guild/attrs/random_seed
    hello-default/.guild/attrs/resolved_deps
    hello-default/.guild/attrs/run_params
    hello-default/.guild/attrs/sourcecode_digest
    hello-default/.guild/attrs/started
    hello-default/.guild/attrs/stopped
    hello-default/.guild/attrs/user
    hello-default/.guild/opref
    hello-default/.guild/output
    hello-default/.guild/output.index
    hello-default/.guild/sourcecode
    hello-default/.guild/sourcecode/guild.yml
    hello-default/.guild/sourcecode/msg.txt
    hello-default/.guild/sourcecode/say.py
    hello-default/output
    <exit 0>
