# Runs ls

    >>> run("guild ls --remote guild-uat")
    ???:
      msg.out
    <exit 0>

    >>> run("guild ls --remote guild-uat --all",
    ...     ignore=["__pycache__", "say.pyc"]) # doctest: +REPORT_UDIFF
    ???:
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
      .guild/attrs/label
      .guild/attrs/op
      .guild/attrs/pip_freeze
      .guild/attrs/platform
      .guild/attrs/random_seed
      .guild/attrs/run_params
      .guild/attrs/sourcecode_digest
      .guild/attrs/started
      .guild/attrs/stopped
      .guild/attrs/user
      .guild/attrs/user_flags
      .guild/job-packages/...
      .guild/opref
      .guild/output
      .guild/output.index
      .guild/sourcecode/
      .guild/sourcecode/README.md
      .guild/sourcecode/data/
      .guild/sourcecode/data/hello-2.txt
      .guild/sourcecode/data/hello.txt
      .guild/sourcecode/guild.yml
      .guild/sourcecode/hello/
      .guild/sourcecode/hello/__init__.py
      .guild/sourcecode/hello/cat.py
      .guild/sourcecode/hello/say.py
      msg.out
    <exit 0>

    >>> run("guild ls --remote guild-uat --sourcecode",
    ...     ignore=["__pycache__", "say.pyc"]) # doctest: +REPORT_UDIFF
    ???/.guild/sourcecode:
      README.md
      data/
      data/hello-2.txt
      data/hello.txt
      guild.yml
      hello/
      hello/__init__.py
      hello/cat.py
      hello/say.py
    <exit 0>
