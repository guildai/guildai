# Completion

## bash

Activation config:

    >>> run("guild completion --shell bash")
    #-*-shell-script-*-
    <BLANKLINE>
    # Extract from bash_completion
    declare -F __reassemble_comp_words_by_ref >/dev/null ||
    __reassemble_comp_words_by_ref() {
        local exclude i j line ref
        if [[ $1 ]]; then
            exclude="[${1//[^$COMP_WORDBREAKS]/}]"
        fi
    <BLANKLINE>
        printf -v "$3" %s "$COMP_CWORD"
        if [[ -v exclude ]]; then
            line=$COMP_LINE
            for ((i = 0, j = 0; i < ${#COMP_WORDS[@]}; i++, j++)); do
                while [[ $i -gt 0 && ${COMP_WORDS[i]} == +($exclude) ]]; do
                    [[ $line != [[:blank:]]* ]] && ((j >= 2)) && ((j--))
                    ref="$2[$j]"
                    printf -v "$ref" %s "${!ref-}${COMP_WORDS[i]}"
                    ((i == COMP_CWORD)) && printf -v "$3" %s "$j"
                    line=${line#*"${COMP_WORDS[i]}"}
                    [[ $line == [[:blank:]]* ]] && ((j++))
                    ((i < ${#COMP_WORDS[@]} - 1)) && ((i++)) || break 2
                done
                ref="$2[$j]"
                printf -v "$ref" %s "${!ref-}${COMP_WORDS[i]}"
                line=${line#*"${COMP_WORDS[i]}"}
                ((i == COMP_CWORD)) && printf -v "$3" %s "$j"
            done
            ((i == COMP_CWORD)) && printf -v "$3" %s "$j"
        else
            for i in "${!COMP_WORDS[@]}"; do
                printf -v "$2[i]" %s "${COMP_WORDS[i]}"
            done
        fi
    }
    <BLANKLINE>
    __apply_alt_cwd() {
        # Applies alt current working directory to COMPREPLY.
        for i in "${!COMPREPLY[@]}"; do
            if [[ -d $1/${COMPREPLY[i]} ]]; then
                COMPREPLY[i]+=/
                compopt -o nospace
            fi
        done
    }
    <BLANKLINE>
    _guild_completion() {
        local cword words
        __reassemble_comp_words_by_ref "=:" words cword
    <BLANKLINE>
        # Use guild to generate comp reply - includes possible directives
        # that are processed later.
        local IFS=$'\n'
        local reply=($(COMP_WORDS="${words[*]}" \
                       COMP_CWORD=$cword \
                       _GUILD_COMPLETE=complete $1))
    <BLANKLINE>
        # Process directories.
        COMPREPLY=()
        local item alt_cwd
        for item in "${reply[@]}"; do
            if [ "${item:0:7}" = '!!file:' ]; then
                COMPREPLY+=($(compgen -f -X '!'"${item:7}" -o plusdirs -- $2))
                compopt -o filenames
            elif [ "${item:0:7}" = '!!dir' ]; then
                COMPREPLY+=($(compgen -d -- $2))
                compopt -o filenames
            elif [ "${item:0:12}" = '!!batchfile:' ]; then
                COMPREPLY+=($(compgen -f -X '!'"${item:12}" -P @ -o plusdirs -- ${2:1}))
                compopt -o filenames
            elif [ "${item:0:10}" = '!!rundirs:' ]; then
                alt_cwd="${item:10}"
                COMPREPLY+=($(cd "$alt_cwd" && compgen -d -X .guild -- $2))
                __apply_alt_cwd "$alt_cwd"
            elif [ "${item:0:13}" = '!!allrundirs:' ]; then
                alt_cwd="${item:13}"
                COMPREPLY+=($(cd "$alt_cwd" && compgen -d -- $2))
                __apply_alt_cwd "$alt_cwd"
            elif [ "${item:0:11}" = '!!runfiles:' ]; then
                alt_cwd="${item:11}"
                COMPREPLY+=($(cd "$alt_cwd" && compgen -f -X .guild -- $2))
                __apply_alt_cwd "$alt_cwd"
            elif [ "$item" = "!!nospace" ]; then
                compopt -o nospace
            elif [ "${item:0:10}" = "!!command:" ]; then
                COMPREPLY+=($(compgen -c -X '!'"${item:10}" -- $2))
            elif [ "$item" = "!!command" ]; then
                COMPREPLY+=($(compgen -c -- $2))
            else
                COMPREPLY+=($item)
            fi
        done
    <BLANKLINE>
    } && complete -o nosort -F _guild_completion guild
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
    #-*-shell-script-*-
    <BLANKLINE>
    # Extract from bash_completion
    declare -F __reassemble_comp_words_by_ref >/dev/null ||
    ...
    } && complete -o nosort -F _guild_completion guild

    >>> cat(path(tmp, "bashrc"))
    [ -s .../bash_completion ] && . .../bash_completion  # Enable completion for guild

## zsh

Activation config:

    >>> run("guild completion --shell zsh")  # doctest: +REPORT_UDIFF
    #-*-shell-script-*-
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
    #-*-shell-script-*-
    ...
    compdef _guild_completion guild;

    >>> cat(path(tmp, "zshrc"))
    [[ -s .../zsh_completion ]] && . .../zsh_completion  # Enable completion for guild

## fish

Activation config:

    >>> run("guild completion --shell fish")  # doctest: +REPORT_UDIFF
    #-*-shell-script-*-
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
    #-*-shell-script-*-
    complete --no-files ... guild)";
    <BLANKLINE>

    >>> cat(path(tmp, "guild.fish"))
    test -s .../fish_completion ;and . .../fish_completion

## Unsupported Shell

    >>> run("guild completion --shell other")
    guild: Invalid value for '-s' / '--shell': invalid choice: other. (choose from bash, zsh, fish)
    Try 'guild completion --help' for more information.
    <exit 2>
