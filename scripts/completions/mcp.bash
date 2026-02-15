#!/usr/bin/env bash
# Bash completion for mcp command

_mcp_completions() {
    local cur prev words cword
    _init_completion || return

    # Main commands
    local commands="init start stop status restart server ide wizard help logs doctor"

    # Server subcommands
    local server_commands="list enable disable info"

    # IDE subcommands
    local ide_commands="setup config detect"

    # Handle completion based on position
    case "${words[1]}" in
        server)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "$server_commands" -- "$cur"))
            elif [[ $cword -eq 3 && ("${words[2]}" == "enable" || "${words[2]}" == "disable" || "${words[2]}" == "info") ]]; then
                # Complete with available server names from config
                # Derive script directory from BASH_SOURCE to work from any directory
                local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
                local config_file="$script_dir/../../config/virtual-servers.txt"
                if [[ -f "$config_file" ]]; then
                    local servers=$(grep -v '^#' "$config_file" | grep -v '^[[:space:]]*$' | cut -d'|' -f1)
                    COMPREPLY=($(compgen -W "$servers" -- "$cur"))
                fi
            fi
            return 0
            ;;
        ide)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "$ide_commands" -- "$cur"))
            fi
            return 0
            ;;
        logs)
            if [[ $cword -eq 2 ]]; then
                # Complete with service names
                COMPREPLY=($(compgen -W "gateway tool-router ollama postgres redis uiforge all" -- "$cur"))
            fi
            return 0
            ;;
        *)
            if [[ $cword -eq 1 ]]; then
                COMPREPLY=($(compgen -W "$commands" -- "$cur"))
            fi
            return 0
            ;;
    esac
}

complete -F _mcp_completions mcp
