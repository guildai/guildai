# Completion

## bash

Activation config:

    >>> run("guild completion --shell bash")  # doctest: +REPORT_UDIFF
    _guild_completion() {
        local IFS=$'
    '
        COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
                       COMP_CWORD=$COMP_CWORD \
                       _GUILD_COMPLETE=complete $1 ) )
        return 0
    }
    <BLANKLINE>
    _guild_completionetup() {
        local COMPLETION_OPTIONS=""
        local BASH_VERSION_ARR=(${BASH_VERSION//./ })
        # Only BASH version 4.4 and later have the nosort option.
        if [ ${BASH_VERSION_ARR[0]} -gt 4 ] || ([ ${BASH_VERSION_ARR[0]} -eq 4 ] && [ ${BASH_VERSION_ARR[1]} -ge 4 ]); then
            COMPLETION_OPTIONS="-o nosort"
        fi
    <BLANKLINE>
        complete $COMPLETION_OPTIONS -F _guild_completion guild
    }
    <BLANKLINE>
    _guild_completionetup;
    <exit 0>

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
    _guild_completion() {
    ...
    _guild_completionetup;

    >>> cat(path(tmp, "bashrc"))
    [ -s .../bash_completion ] && . .../bash_completion  # Enable completion for guild

## zsh

Activation config:

    >>> run("guild completion --shell zsh")  # doctest: +REPORT_UDIFF
    #compdef guild
    <BLANKLINE>
    _guild_completion() {
        local -a completions
        local -a completions_with_descriptions
        local -a response
        (( ! $+commands[guild] )) && return 1
    <BLANKLINE>
        response=("${(@f)$( env COMP_WORDS="${words[*]}" \
                            COMP_CWORD=$((CURRENT-1)) \
                            _GUILD_COMPLETE="complete_zsh" \
                            guild )}")
    <BLANKLINE>
        for key descr in ${(kv)response}; do
          if [[ "$descr" == "_" ]]; then
              completions+=("$key")
          else
              completions_with_descriptions+=("$key":"$descr")
          fi
        done
    <BLANKLINE>
        if [ -n "$completions_with_descriptions" ]; then
            _describe -V unsorted completions_with_descriptions -U
        fi
    <BLANKLINE>
        if [ -n "$completions" ]; then
            compadd -U -V unsorted -a completions
        fi
        compstate[insert]="automenu"
    }
    <BLANKLINE>
    compdef _guild_completion guild;
    <exit 0>

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
    #compdef guild
    ...
    compdef _guild_completion guild;

    >>> cat(path(tmp, "zshrc"))
    [[ -s .../zsh_completion ]] && . .../zsh_completion  # Enable completion for guild

## fish

Activation config:

    >>> run("guild completion --shell fish")  # doctest: +REPORT_UDIFF
    complete --no-files --command guild --arguments "(env _GUILD_COMPLETE=complete_fish COMP_WORDS=(commandline -cp) COMP_CWORD=(commandline -t) guild)";
    <exit 0>

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
    complete --no-files ... guild)";
    <BLANKLINE>

    >>> cat(path(tmp, "guild.fish"))
    test -s .../fish_completion ;and . .../fish_completion

## Unsupported Shell

    >>> run("guild completion --shell other")
    guild: Invalid value for '-s' / '--shell': invalid choice: other. (choose from bash, zsh, fish)
    Try 'guild completion --help' for more information.
    <exit 2>
