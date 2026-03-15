export const dynamic = 'force-dynamic';

import { NextRequest, NextResponse } from 'next/server';

const GATEWAY_URL = process.env.MCP_GATEWAY_URL ?? 'http://localhost:4444';

function gatewayHeaders(req: NextRequest): HeadersInit {
  const auth = req.headers.get('authorization');
  const headers: Record<string, string> = { 'content-type': 'application/json' };
  if (auth) headers.authorization = auth;
  return headers;
}

export async function PATCH(request: NextRequest, { params }: { params: { name: string } }) {
  try {
    const body = await request.json();
    const response = await fetch(`${GATEWAY_URL}/servers/${params.name}/enabled`, {
      method: 'PATCH',
      headers: gatewayHeaders(request),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      return NextResponse.json({ error: 'Gateway error' }, { status: response.status });
    }
    return NextResponse.json(await response.json());
  } catch (error) {
    console.error('Failed to toggle server enabled:', error);
    return NextResponse.json({ error: 'Failed to toggle server' }, { status: 500 });
  }
}
