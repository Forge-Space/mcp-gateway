#compdef mcp

# Zsh completion for mcp command

_mcp() {
    local -a commands server_commands ide_commands log_services

    commands=(
        'init:Initialize MCP Gateway project'
        'start:Start the gateway stack'
        'stop:Stop the gateway stack'
        'status:Check gateway health and status'
        'restart:Restart the gateway stack'
        'server:Manage virtual servers'
        'ide:IDE configuration tools'
        'wizard:Interactive setup wizard'
        'logs:View gateway logs'
        'doctor:Run health checks and diagnostics'
        'help:Show help message'
    )

    server_commands=(
        'list:List all virtual servers'
        'enable:Enable a virtual server'
        'disable:Disable a virtual server'
        'info:Get server details'
    )

    ide_commands=(
        'setup:Interactive IDE setup wizard'
        'config:Generate IDE configuration'
        'detect:Auto-detect installed IDEs'
    )

    log_services=(
        'gateway:Gateway logs'
        'tool-router:Tool router logs'
        'ollama:Ollama logs'
        'postgres:PostgreSQL logs'
        'redis:Redis logs'
        'uiforge:UIForge logs'
        'all:All service logs'
    )

    case $words[2] in
        server)
            case $words[3] in
                enable|disable|info)
                    # Complete with server names from config
                    # Derive script directory to work from any directory
                    local script_dir="${0:A:h}"
                    local config_file="$script_dir/../../config/virtual-servers.txt"
                    if [[ -f "$config_file" ]]; then
                        local -a servers
                        servers=(${(f)"$(grep -v '^#' "$config_file" | grep -v '^[[:space:]]*$' | cut -d'|' -f1)"})
                        _describe 'servers' servers
                    fi
                    ;;
                *)
                    _describe 'server commands' server_commands
                    ;;
            esac
            ;;
        ide)
            _describe 'ide commands' ide_commands
            ;;
        logs)
            _describe 'log services' log_services
            ;;
        *)
            _describe 'commands' commands
            ;;
    esac
}

_mcp "$@"
