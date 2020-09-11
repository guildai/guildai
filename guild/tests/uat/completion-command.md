# Completion

## bash

Activation config:

    >>> quiet("guild completion --shell bash")

Init script mod:

    >>> tmp = mkdtemp()
    >>> run("GUILD_CONFIG={tmp}/config.yml "
    ...     "guild completion --shell bash --install --shell-init {tmp}/bashrc"
    ...     .format(tmp=tmp))
    Writing completion script to .../bash_completion
    Updating .../bashrc to support Guild command completion
    Guild command completion is installed - changes will take effect the next
    time you open a terminal session
    <exit 0>

    >>> find(tmp)
    bash_completion
    bashrc

    >>> cat(path(tmp, "bash_completion"))
    #-*-shell-script-*-
    ...

    >>> cat(path(tmp, "bashrc"))
    [ -s .../bash_completion ] && . .../bash_completion  # Enable completion for guild

## zsh

Activation config:

    >>> quiet("guild completion --shell zsh")  # doctest: +REPORT_UDIFF

Init script mod:

    >>> tmp = mkdtemp()
    >>> run("GUILD_CONFIG={tmp}/config.yml "
    ...     "guild completion --shell zsh --install --shell-init {tmp}/zshrc"
    ...     .format(tmp=tmp))
    Writing completion script to .../zsh_completion
    Updating .../zshrc to support Guild command completion
    Guild command completion is installed - changes will take effect the next
    time you open a terminal session
    <exit 0>

    >>> find(tmp)
    zsh_completion
    zshrc

    >>> cat(path(tmp, "zsh_completion"))
    #-*-shell-script-*-
    ...

    >>> cat(path(tmp, "zshrc"))
    [[ -s .../zsh_completion ]] && . .../zsh_completion  # Enable completion for guild

## fish

Activation config:

    >>> quiet("guild completion --shell fish")  # doctest: +REPORT_UDIFF

Init script mod:

    >>> tmp = mkdtemp()
    >>> run("GUILD_CONFIG={tmp}/config.yml "
    ...     "guild completion --shell fish --install --shell-init {tmp}/guild.fish"
    ...     .format(tmp=tmp))
    Writing completion script to .../fish_completion
    Updating .../guild.fish to support Guild command completion
    Guild command completion is installed - changes will take effect the next
    time you open a terminal session
    <exit 0>

    >>> find(tmp)
    fish_completion
    guild.fish

    >>> cat(path(tmp, "fish_completion"))
    #-*-shell-script-*-
    ...

    >>> cat(path(tmp, "guild.fish"))
    test -s .../fish_completion ;and . .../fish_completion

## Unsupported Shell

    >>> run("guild completion --shell other")
    guild: Invalid value for '-s' / '--shell': invalid choice: other. (choose from bash, zsh, fish)
    Try 'guild completion --help' for more information.
    <exit 2>
