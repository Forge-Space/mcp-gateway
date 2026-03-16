// MCP Gateway Client - bridges IDE MCP clients to the self-hosted gateway
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const GATEWAY_URL = process.env.GATEWAY_URL ?? "http://localhost:4444";
const GATEWAY_TOKEN = process.env.GATEWAY_TOKEN;
const REQUEST_TIMEOUT_MILLISECONDS = 30000;

interface JsonRpcRequest {
  jsonrpc: "2.0";
  id: number;
  method: string;
  params?: unknown;
}

interface JsonRpcResponse {
  jsonrpc: string;
  id: number;
  result?: unknown;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
}

interface ToolDefinition {
  name: string;
  description?: string;
  inputSchema?: {
    type: string;
    properties?: Record<string, unknown>;
    required?: string[];
    [key: string]: unknown;
  };
}

interface ListToolsResult {
  tools: ToolDefinition[];
}

interface CallToolResult {
  content: Array<{
    type: string;
    text?: string;
    [key: string]: unknown;
  }>;
  isError?: boolean;
}

const server = new Server(
  {
    name: "mcp-gateway-client",
    version: "1.28.2",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

// Helper to send requests to the gateway
async function sendGatewayRequest(
  method: string,
  path: string,
  body: JsonRpcRequest,
): Promise<JsonRpcResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    REQUEST_TIMEOUT_MILLISECONDS,
  );

  try {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (GATEWAY_TOKEN !== undefined && GATEWAY_TOKEN.length > 0) {
      headers["Authorization"] = `Bearer ${GATEWAY_TOKEN}`;
    }

    const response = await fetch(`${GATEWAY_URL}/${method}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(
        `Gateway returned HTTP ${response.status}: ${response.statusText}`,
      );
    }

    const contentType = response.headers.get("content-type");
    if (!(contentType?.includes("application/json") === true)) {
      throw new Error(
        `Gateway returned non-JSON response: ${contentType ?? "null"}`,
      );
    }

    const data: unknown = await response.json();

    if (typeof data !== "object" || data === null) {
      throw new Error("Gateway returned invalid response: not an object");
    }

    const responseData = data as JsonRpcResponse;

    if (responseData.jsonrpc !== "2.0") {
      throw new Error(
        `Gateway returned invalid JSON-RPC version: ${String(responseData.jsonrpc)}`,
      );
    }

    if (responseData.error) {
      throw new Error(
        `Gateway returned error: ${JSON.stringify(responseData.error)}`,
      );
    }

    return responseData;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(
        `Gateway request timeout after ${REQUEST_TIMEOUT_MILLISECONDS}ms`,
        { cause: error },
      );
    }
    throw error;
  }
}

// List available tools from gateway
server.setRequestHandler(ListToolsRequestSchema, async () => {
  try {
    const response = await sendGatewayRequest("POST", "", {
      jsonrpc: "2.0",
      id: Date.now(),
      method: "tools/list",
      params: {},
    });

    if (response.result === undefined || response.result === null) {
      throw new Error("Invalid response from gateway");
    }

    const result = response.result as ListToolsResult;

    return {
      tools: result.tools.map((tool) => ({
        name: tool.name,
        description: tool.description ?? "",
        inputSchema: tool.inputSchema ?? {
          type: "object",
          properties: {},
        },
      })),
    };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error listing tools";
    return {
      tools: [
        {
          name: "gateway_error",
          description: `Failed to connect to MCP gateway: ${message}`,
          inputSchema: {
            type: "object",
            properties: {},
          },
        },
      ],
    };
  }
});

// Forward tool calls to gateway
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  // Handle the error tool gracefully
  if (name === "gateway_error") {
    return {
      content: [
        {
          type: "text",
          text: "Cannot execute tools: MCP gateway is not accessible. Please check that the gateway is running and GATEWAY_URL is configured correctly.",
        },
      ],
      isError: true,
    };
  }

  try {
    const response = await sendGatewayRequest("POST", "", {
      jsonrpc: "2.0",
      id: Date.now(),
      method: "tools/call",
      params: {
        name,
        arguments: args ?? {},
      },
    });

    if (response.result === undefined || response.result === null) {
      throw new Error("Invalid response from gateway: missing result");
    }

    const result = response.result as CallToolResult;
    return {
      content: result.content,
      isError: result.isError,
    };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error calling tool";
    return {
      content: [
        {
          type: "text",
          text: `Error calling tool ${name}: ${message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start the server
const transport = new StdioServerTransport();
await server.connect(transport);
