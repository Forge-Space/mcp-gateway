# Fish completion for mcp command

# Main commands
complete -c mcp -f -n "__fish_use_subcommand" -a "init" -d "Initialize MCP Gateway project"
complete -c mcp -f -n "__fish_use_subcommand" -a "start" -d "Start the gateway stack"
complete -c mcp -f -n "__fish_use_subcommand" -a "stop" -d "Stop the gateway stack"
complete -c mcp -f -n "__fish_use_subcommand" -a "status" -d "Check gateway health and status"
complete -c mcp -f -n "__fish_use_subcommand" -a "restart" -d "Restart the gateway stack"
complete -c mcp -f -n "__fish_use_subcommand" -a "server" -d "Manage virtual servers"
complete -c mcp -f -n "__fish_use_subcommand" -a "ide" -d "IDE configuration tools"
complete -c mcp -f -n "__fish_use_subcommand" -a "wizard" -d "Interactive setup wizard"
complete -c mcp -f -n "__fish_use_subcommand" -a "logs" -d "View gateway logs"
complete -c mcp -f -n "__fish_use_subcommand" -a "doctor" -d "Run health checks and diagnostics"
complete -c mcp -f -n "__fish_use_subcommand" -a "help" -d "Show help message"

# Server subcommands - only show when no subcommand is present yet
complete -c mcp -f -n "__fish_seen_subcommand_from server; and not __fish_seen_subcommand_from list enable disable info" -a "list" -d "List all virtual servers"
complete -c mcp -f -n "__fish_seen_subcommand_from server; and not __fish_seen_subcommand_from list enable disable info" -a "enable" -d "Enable a virtual server"
complete -c mcp -f -n "__fish_seen_subcommand_from server; and not __fish_seen_subcommand_from list enable disable info" -a "disable" -d "Disable a virtual server"
complete -c mcp -f -n "__fish_seen_subcommand_from server; and not __fish_seen_subcommand_from list enable disable info" -a "info" -d "Get server details"

# IDE subcommands
complete -c mcp -f -n "__fish_seen_subcommand_from ide" -a "setup" -d "Interactive IDE setup wizard"
complete -c mcp -f -n "__fish_seen_subcommand_from ide" -a "config" -d "Generate IDE configuration"
complete -c mcp -f -n "__fish_seen_subcommand_from ide" -a "detect" -d "Auto-detect installed IDEs"

# Logs subcommands
complete -c mcp -f -n "__fish_seen_subcommand_from logs" -a "gateway" -d "Gateway logs"
complete -c mcp -f -n "__fish_seen_subcommand_from logs" -a "tool-router" -d "Tool router logs"
complete -c mcp -f -n "__fish_seen_subcommand_from logs" -a "ollama" -d "Ollama logs"
complete -c mcp -f -n "__fish_seen_subcommand_from logs" -a "postgres" -d "PostgreSQL logs"
complete -c mcp -f -n "__fish_seen_subcommand_from logs" -a "redis" -d "Redis logs"
complete -c mcp -f -n "__fish_seen_subcommand_from logs" -a "uiforge" -d "UIForge logs"
complete -c mcp -f -n "__fish_seen_subcommand_from logs" -a "all" -d "All service logs"

# Server name completion for enable/disable/info
function __mcp_server_names
    # Derive script directory to work from any directory
    set -l script_dir (dirname (status -f))
    set -l config_file "$script_dir/../../config/virtual-servers.txt"
    if test -f "$config_file"
        grep -v '^#' "$config_file" | grep -v '^[[:space:]]*$' | cut -d'|' -f1
    end
end

complete -c mcp -f -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from enable" -a "(__mcp_server_names)"
complete -c mcp -f -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from disable" -a "(__mcp_server_names)"
complete -c mcp -f -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from info" -a "(__mcp_server_names)"
