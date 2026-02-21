#!/usr/bin/env node

/**
 * MCP Gateway Client - NPX wrapper for connecting to MCP Gateway
 *
 * This client connects to a running MCP Gateway instance and proxies
 * MCP protocol messages over HTTP/SSE transport.
 *
 * Usage (Local - No Auth):
 *   npx @forge-mcp-gateway/client --url http://localhost:4444/servers/<UUID>/mcp
 *
 * Usage (Remote - With Auth):
 *   npx @forge-mcp-gateway/client --url https://gateway.example.com/servers/<UUID>/mcp --token <JWT>
 *
 * Environment Variables:
 *   MCP_GATEWAY_URL - Gateway server URL (required)
 *   MCP_GATEWAY_TOKEN - JWT authentication token (optional, for remote/secured gateways)
 *   MCP_GATEWAY_TIMEOUT - Request timeout in ms (default: 120000)
 */

import { ForgeCore } from '@forgespace/core';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fetch from 'node-fetch';

// Helper function to parse CLI arguments safely
function parseCliArg(argName: string): string | undefined {
  const arg = process.argv.find((a) => a.startsWith(`--${argName}=`));
  if (arg === undefined) {
    return undefined;
  }
  const value = arg.split('=').slice(1).join('='); // Handle URLs with = in them
  return value.length > 0 ? value : undefined;
}

// Configuration from environment variables or CLI args
const GATEWAY_URL = process.env.MCP_GATEWAY_URL ?? parseCliArg('url');
const GATEWAY_TOKEN = process.env.MCP_GATEWAY_TOKEN ?? parseCliArg('token');
const REQUEST_TIMEOUT_MILLISECONDS = parseInt(process.env.MCP_GATEWAY_TIMEOUT ?? '120000', 10);

// Validate timeout is reasonable
if (
  isNaN(REQUEST_TIMEOUT_MILLISECONDS) ||
  REQUEST_TIMEOUT_MILLISECONDS < 1000 ||
  REQUEST_TIMEOUT_MILLISECONDS > 600000
) {
  console.error('Error: MCP_GATEWAY_TIMEOUT must be between 1000 and 600000 ms');
  process.exit(1);
}

if (GATEWAY_URL === undefined || GATEWAY_URL.length === 0) {
  console.error('Error: MCP_GATEWAY_URL is required');
  console.error('\nUsage (Local):');
  console.error('  npx @forge-mcp-gateway/client --url=http://localhost:4444/servers/<UUID>/mcp');
  console.error('\nUsage (Remote with Auth):');
  console.error('  npx @forge-mcp-gateway/client --url=<gateway-url> --token=<jwt>');
  console.error('\nOr set environment variables:');
  console.error('  MCP_GATEWAY_URL=http://localhost:4444/servers/<UUID>/mcp');
  console.error('  MCP_GATEWAY_TOKEN=<jwt-token>  # Optional for local, required for remote');
  process.exit(1);
}

// Create MCP server instance
const server = new Server(
  {
    name: 'forge-mcp-gateway-client',
    version: '0.1.0',
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {},
    },
  }
);

// Initialize ForgeCore
const forgeCore = new ForgeCore({
  gatewayUrl: GATEWAY_URL,
  authToken: GATEWAY_TOKEN,
  timeout: REQUEST_TIMEOUT_MILLISECONDS,
});

// Define response type for gateway requests
interface GatewayResponse {
  jsonrpc: string;
  id: number;
  result?: unknown;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
}

// Helper function to make requests to gateway (with optional authentication)
async function sendGatewayRequest(
  method: string,
  endpoint: string,
  body?: unknown
): Promise<GatewayResponse> {
  const url = `${GATEWAY_URL}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MILLISECONDS);

  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };

    // Only add Authorization header if token is provided
    if (GATEWAY_TOKEN !== undefined && GATEWAY_TOKEN.length > 0) {
      headers.Authorization = `Bearer ${GATEWAY_TOKEN}`;
    }

    const response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : null,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Gateway request failed: ${response.status} ${response.statusText}\n${errorText}`
      );
    }

    const contentType = response.headers.get('content-type');
    if (contentType === null || contentType.includes('application/json') === false) {
      throw new Error(`Gateway returned non-JSON response: ${contentType ?? 'null'}`);
    }

    const responseData = (await response.json()) as GatewayResponse;

    // Validate JSON-RPC response structure
    if (typeof responseData !== 'object' || responseData === null) {
      throw new Error('Gateway returned invalid response: not an object');
    }

    if (typeof responseData.jsonrpc !== 'string' || responseData.jsonrpc !== '2.0') {
      throw new Error(`Gateway returned invalid JSON-RPC version: ${String(responseData.jsonrpc)}`);
    }

    if ('error' in responseData && responseData.error !== undefined) {
      throw new Error(`Gateway returned error: ${JSON.stringify(responseData.error)}`);
    }

    return responseData;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`Gateway request timeout after ${REQUEST_TIMEOUT_MILLISECONDS}ms`);
    }
    throw error;
  }
}

// List available tools from gateway
server.setRequestHandler(ListToolsRequestSchema, async () => {
  try {
    const response = await sendGatewayRequest('POST', '', {
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'tools/list',
    });

    if (typeof response !== 'object' || response === null) {
      throw new Error('Invalid response from gateway');
    }

    return (response.result ?? { tools: [] }) as { tools: unknown[] };
  } catch (error) {
    console.error('Error listing tools:', error);
    return { tools: [] };
  }
});

// Call a tool via gateway
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const response = await sendGatewayRequest('POST', '', {
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'tools/call',
      params: {
        name: request.params.name,
        arguments: request.params.arguments,
      },
    });

    if (typeof response !== 'object' || response.result === undefined) {
      throw new Error('Invalid response from gateway: missing result');
    }

    return response.result as {
      content: { type: string; text?: string; [key: string]: unknown }[];
      isError?: boolean;
    };
  } catch (error) {
    console.error('Error calling tool:', error);
    throw error;
  }
});

// List available resources from gateway
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  try {
    const response = await sendGatewayRequest('POST', '', {
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'resources/list',
    });
    return (response.result ?? { resources: [] }) as { resources: unknown[] };
  } catch (error) {
    console.error('Error listing resources:', error);
    return { resources: [] };
  }
});

// Read a resource via gateway
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  try {
    const response = await sendGatewayRequest('POST', '', {
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'resources/read',
      params: {
        uri: request.params.uri,
      },
    });
    if (response.result === undefined) {
      throw new Error('Invalid response from gateway: missing result');
    }

    return response.result as {
      contents: {
        uri: string;
        mimeType?: string;
        text?: string;
        blob?: string;
        [key: string]: unknown;
      }[];
    };
  } catch (error) {
    console.error('Error reading resource:', error);
    throw error;
  }
});

// List available prompts from gateway
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  try {
    const response = await sendGatewayRequest('POST', '', {
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'prompts/list',
    });
    return (response.result ?? { prompts: [] }) as { prompts: unknown[] };
  } catch (error) {
    console.error('Error listing prompts:', error);
    return { prompts: [] };
  }
});

// Get a specific prompt via gateway
server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  try {
    const response = await sendGatewayRequest('POST', '', {
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'prompts/get',
      params: {
        name: request.params.name,
        arguments: request.params.arguments,
      },
    });
    if (response.result === undefined) {
      throw new Error('Invalid response from gateway: missing result');
    }

    return response.result as {
      description?: string;
      messages: {
        role: string;
        content: { type: string; text?: string; [key: string]: unknown };
        [key: string]: unknown;
      }[];
    };
  } catch (error) {
    console.error('Error getting prompt:', error);
    throw error;
  }
});

// Start the server with stdio transport
async function main(): Promise<void> {
  // Initialize ForgeCore
  try {
    await forgeCore.initialize();
    console.error('ForgeCore initialized successfully');
  } catch (error) {
    console.error('Failed to initialize ForgeCore:', error);
    // Continue without ForgeCore if initialization fails
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error(`MCP Gateway Client connected to: ${GATEWAY_URL}`);
  console.error(
    `Authentication: ${
      GATEWAY_TOKEN !== undefined && GATEWAY_TOKEN.length > 0
        ? 'Enabled (JWT)'
        : 'Disabled (Local mode)'
    }`
  );
  console.error(`Timeout: ${REQUEST_TIMEOUT_MILLISECONDS}ms`);
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
