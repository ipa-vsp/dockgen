_dct() {
    local cur prev words cword
    _init_completion 2>/dev/null || {
        COMPREPLY=()
        cur="${COMP_WORDS[COMP_CWORD]}"
        prev="${COMP_WORDS[COMP_CWORD-1]}"
    }

    local top_cmds="new config add validate info"

    case "$prev" in
        dockgen)
            COMPREPLY=($(compgen -W "$top_cmds" -- "$cur"))
            return ;;
        add)
            COMPREPLY=($(compgen -W "gpu display volume" -- "$cur"))
            return ;;
        -w|--workspace)
            COMPREPLY=($(compgen -d -- "$cur"))
            return ;;
        volume)
            # suggest current directory as bind-mount source
            COMPREPLY=($(compgen -d -- "$cur"))
            return ;;
    esac

    # If first word after dockgen is a subcommand, complete its flags
    if [[ ${#COMP_WORDS[@]} -ge 3 ]]; then
        local subcmd="${COMP_WORDS[1]}"
        case "$subcmd" in
            new)
                COMPREPLY=($(compgen -W "--force -w --workspace" -- "$cur")) ;;
            config|validate|info)
                COMPREPLY=($(compgen -W "-w --workspace" -- "$cur")) ;;
            add)
                COMPREPLY=($(compgen -W "gpu display volume" -- "$cur")) ;;
        esac
    fi
}

complete -F _dct dockgen
