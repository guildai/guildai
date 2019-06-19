# Runs ls

    >>> run("guild ls --remote guild-uat-ssh")
    ???:
      msg.txt
      output
    <exit 0>

    >>> run("guild ls --remote guild-uat-ssh --all") # doctest: +REPORT_UDIFF
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
      .guild/attrs/opdef
      .guild/attrs/platform
      .guild/attrs/random_seed
      .guild/attrs/run_params
      .guild/attrs/started
      .guild/attrs/stopped
      .guild/attrs/user
      .guild/opref
      .guild/output
      .guild/output.index
      .guild/sourcecode/
      .guild/sourcecode/guild.yml
      .guild/sourcecode/msg.txt
      .guild/sourcecode/say.py
      msg.txt
      output
    <exit 0>

    >>> run("guild ls --remote guild-uat-ssh --sourcecode") # doctest: +REPORT_UDIFF
    ???:
      .guild/sourcecode/
      .guild/sourcecode/guild.yml
      .guild/sourcecode/msg.txt
      .guild/sourcecode/say.py
    <exit 0>
