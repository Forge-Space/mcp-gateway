export const dynamic = 'force-dynamic';

import { NextRequest, NextResponse } from 'next/server';

// Mock data - in production this would come from the MCP Gateway API
const mockServers = [
  {
    id: 'cursor-default',
    name: 'cursor-default',
    url: 'http://localhost:4444/sse/cursor-default',
    enabled: true,
    tools: 45,
    description: 'Full-featured development stack with all tools',
  },
  {
    id: 'cursor-router',
    name: 'cursor-router',
    url: 'http://localhost:4444/sse/cursor-router',
    enabled: true,
    tools: 2,
    description: 'AI-powered tool router for intelligent tool selection',
  },
  {
    id: 'nodejs-typescript',
    name: 'nodejs-typescript',
    url: 'http://localhost:4444/sse/nodejs-typescript',
    enabled: true,
    tools: 8,
    description: 'Node.js and TypeScript development tools',
  },
];

export async function GET(request: NextRequest) {
  try {
    // In production, fetch from actual MCP Gateway API
    // const response = await fetch('http://localhost:4444/api/servers')
    // const servers = await response.json()

    return NextResponse.json(mockServers);
  } catch (error) {
    console.error('Failed to fetch servers:', error);
    return NextResponse.json({ error: 'Failed to fetch servers' }, { status: 500 });
  }
}
