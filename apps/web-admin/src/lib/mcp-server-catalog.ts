export type ServerTypeId =
  | 'filesystem'
  | 'github'
  | 'fetch'
  | 'memory'
  | 'postgres'
  | 'mongodb'
  | 'sequential-thinking'
  | 'custom';

export interface EnvVarSpec {
  key: string;
  label: string;
  placeholder: string;
  required: boolean;
  secret: boolean;
  description?: string;
}

export interface ServerTypeDefinition {
  id: ServerTypeId;
  name: string;
  description: string;
  icon: string;
  category: 'tools' | 'data' | 'ai' | 'custom';
  defaultPort: number;
  dockerImage: string;
  defaultTransport: 'SSE' | 'STREAMABLEHTTP';
  envVars: EnvVarSpec[];
  defaultTools: string[];
  badge?: string;
}

export const SERVER_TYPE_CATALOG: ServerTypeDefinition[] = [
  {
    id: 'filesystem',
    name: 'Filesystem',
    description: 'Access and manipulate local files and directories',
    icon: 'FolderOpen',
    category: 'tools',
    defaultPort: 8040,
    dockerImage: 'forge-mcp-gateway-translate:latest',
    defaultTransport: 'SSE',
    envVars: [
      {
        key: 'FILESYSTEM_ROOT',
        label: 'Root Path',
        placeholder: '/workspace',
        required: true,
        secret: false,
        description: 'Absolute path to the directory to expose',
      },
    ],
    defaultTools: ['read_file', 'write_file', 'list_directory', 'create_directory', 'delete_file'],
  },
  {
    id: 'github',
    name: 'GitHub',
    description: 'Interact with GitHub repositories, issues, and pull requests',
    icon: 'Github',
    category: 'tools',
    defaultPort: 8041,
    dockerImage: 'forge-mcp-gateway-translate:latest',
    defaultTransport: 'SSE',
    envVars: [
      {
        key: 'GITHUB_PERSONAL_ACCESS_TOKEN',
        label: 'Personal Access Token',
        placeholder: 'ghp_...',
        required: true,
        secret: true,
        description: 'GitHub PAT with repo, issues, and pull_requests scopes',
      },
    ],
    defaultTools: ['list_repos', 'get_file', 'create_issue', 'list_pull_requests', 'search_code'],
    badge: 'Popular',
  },
  {
    id: 'fetch',
    name: 'Fetch / HTTP',
    description: 'Make HTTP requests and fetch web content',
    icon: 'Globe',
    category: 'tools',
    defaultPort: 8042,
    dockerImage: 'forge-mcp-gateway-translate:latest',
    defaultTransport: 'SSE',
    envVars: [
      {
        key: 'FETCH_ALLOWED_DOMAINS',
        label: 'Allowed Domains',
        placeholder: 'api.example.com,*.github.com',
        required: false,
        secret: false,
        description: 'Comma-separated list of allowed domains (leave empty for all)',
      },
    ],
    defaultTools: ['fetch_url', 'fetch_json', 'post_request'],
  },
  {
    id: 'memory',
    name: 'Memory Store',
    description: 'Persistent key-value memory store for AI context',
    icon: 'Brain',
    category: 'ai',
    defaultPort: 8043,
    dockerImage: 'forge-mcp-gateway-translate:latest',
    defaultTransport: 'SSE',
    envVars: [
      {
        key: 'MEMORY_STORAGE_PATH',
        label: 'Storage Path',
        placeholder: '/data/memory',
        required: false,
        secret: false,
        description: 'Path to persist memory data (defaults to /data/memory)',
      },
    ],
    defaultTools: ['store_memory', 'retrieve_memory', 'list_memories', 'delete_memory'],
    badge: 'AI',
  },
  {
    id: 'postgres',
    name: 'PostgreSQL',
    description: 'Query and manage PostgreSQL databases',
    icon: 'Database',
    category: 'data',
    defaultPort: 8044,
    dockerImage: 'forge-mcp-gateway-translate:latest',
    defaultTransport: 'SSE',
    envVars: [
      {
        key: 'POSTGRES_CONNECTION_STRING',
        label: 'Connection String',
        placeholder: 'postgresql://user:password@host:5432/dbname',
        required: true,
        secret: true,
        description: 'Full PostgreSQL connection string',
      },
    ],
    defaultTools: ['execute_query', 'list_tables', 'describe_table', 'insert_row', 'update_row'],
  },
  {
    id: 'mongodb',
    name: 'MongoDB',
    description: 'Query and manage MongoDB collections',
    icon: 'Database',
    category: 'data',
    defaultPort: 8045,
    dockerImage: 'forge-mcp-gateway-translate:latest',
    defaultTransport: 'SSE',
    envVars: [
      {
        key: 'MONGODB_CONNECTION_STRING',
        label: 'Connection String',
        placeholder: 'mongodb://user:password@host:27017/dbname',
        required: true,
        secret: true,
        description: 'Full MongoDB connection string',
      },
    ],
    defaultTools: [
      'find_documents',
      'insert_document',
      'update_document',
      'delete_document',
      'list_collections',
    ],
  },
  {
    id: 'sequential-thinking',
    name: 'Sequential Thinking',
    description: 'Step-by-step reasoning and problem decomposition tools',
    icon: 'Lightbulb',
    category: 'ai',
    defaultPort: 8046,
    dockerImage: 'forge-mcp-gateway-translate:latest',
    defaultTransport: 'SSE',
    envVars: [],
    defaultTools: ['think_step_by_step', 'decompose_problem', 'evaluate_solution'],
    badge: 'AI',
  },
  {
    id: 'custom',
    name: 'Custom Server',
    description: 'Define your own MCP server with a custom Docker image and command',
    icon: 'Code',
    category: 'custom',
    defaultPort: 8050,
    dockerImage: '',
    defaultTransport: 'SSE',
    envVars: [],
    defaultTools: [],
    badge: 'Advanced',
  },
];

export function getServerType(id: ServerTypeId): ServerTypeDefinition | undefined {
  return SERVER_TYPE_CATALOG.find((s) => s.id === id);
}

export function getNextAvailablePort(usedPorts: number[]): number {
  let port = 8040;
  while (usedPorts.includes(port)) {
    port++;
  }
  return port;
}
