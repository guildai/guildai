---
doctest-type: bash
---

# Project Level User Config

As of 0.7.5, Guild supports defining user config within a project
using a file named `guild-config.yml`. This project illustrates this
feature.

Refer to [`guild-config.yml`](guild-config.yml) for configuration
details.

`guild-config.yml` replaces `~/.guild/config.yml` outright. Any config
defined in `~/.guild/config.yml` must be redefined in
`guild-config.yml` if needed.

Remotes:

    $ guild remotes
    localhost  ssh  Run on localhost over ssh

Check config:

    $ guild check
    guild_version:             ...
    latest_guild_version:      unchecked (offline)

Diff command:

    $ guild run hello --run-id aaa -y
    Hello Guild!

    $ guild run hello --run-id bbb -y
    Hello Guild!

    $ guild diff
    Using echo: .../runs/aaa .../runs/bbb
