# Runs ls

`ls` is generated from the run manfiest.

    >>> run("guild cat -p .guild/manifest --remote guild-uat")
    s README.md 60eb176260122f67440d8cea65f7dc86b8331b9c README.md
    s guild.yml 3f8bc75baa61cad67c2d596b353f3b3f3ba2fbd0 guild.yml
    s data/hello-2.txt 3c22f452dc3a375d0d35a832ba0bf5cbb79b553f data/hello-2.txt
    s data/hello.txt 7e1a1a698162c39e88d7855ccd0d73bfa72db1a1 data/hello.txt
    s hello/__init__.py da39a3ee5e6b4b0d3255bfef95601890afd80709 hello/__init__.py
    s hello/cat.py 51d27379080c44b20d868246bd6981884e820be5 hello/cat.py
    s hello/say.py 52dc1bf9d9017c3cb56530ad70d3f1bb84b1974e hello/say.py
    d msg.out 7e1a1a698162c39e88d7855ccd0d73bfa72db1a1 operation:hello-file

    >>> run("guild ls --remote guild-uat -n")
    README.md
    data/
    data/hello-2.txt
    data/hello.txt
    guild.yml
    hello/
    hello/__init__.py
    hello/__pycache__/
    hello/__pycache__/__init__.cpython-310.pyc
    hello/cat.py
    hello/say.py
    msg.out

    >>> run("guild ls --remote guild-uat -n --sourcecode")
    README.md
    data/hello-2.txt
    data/hello.txt
    guild.yml
    hello/__init__.py
    hello/cat.py
    hello/say.py

    >>> run("guild ls --remote guild-uat -n --dependencies")
    msg.out

    >>> run("guild ls --remote guild-uat -n --generated",
    ...     ignore=["__pycache__", "say.pyc"])
    <exit 0>

    >>> run("guild ls --remote guild-uat --all -n",
    ...     ignore=["__pycache__", "say.pyc"]) # doctest: +REPORT_UDIFF
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
    .guild/attrs/platform
    .guild/attrs/plugins
    .guild/attrs/random_seed
    .guild/attrs/run_params
    .guild/attrs/sourcecode_digest
    .guild/attrs/started
    .guild/attrs/stopped
    .guild/attrs/user
    .guild/attrs/user_flags
    .guild/job-packages/...
    .guild/manifest
    .guild/opref
    .guild/output
    .guild/output.index
    README.md
    data/
    data/hello-2.txt
    data/hello.txt
    guild.yml
    hello/
    hello/__init__.py
    hello/cat.py
    hello/say.py
    msg.out
