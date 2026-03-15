export const dynamic = 'force-dynamic';

import { NextRequest, NextResponse } from 'next/server';

const GATEWAY_URL = process.env.MCP_GATEWAY_URL ?? 'http://localhost:4444';

function gatewayHeaders(req: NextRequest): HeadersInit {
  const auth = req.headers.get('authorization');
  return auth ? { authorization: auth } : {};
}

export async function PATCH(request: NextRequest) {
  try {
    const body = await request.json();
    const response = await fetch(`${GATEWAY_URL}/cloud/strategy`, {
      method: 'PATCH',
      headers: { ...gatewayHeaders(request), 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      return NextResponse.json({ error: 'Gateway error' }, { status: response.status });
    }
    return NextResponse.json(await response.json());
  } catch (error) {
    console.error('Failed to update cloud routing strategy:', error);
    return NextResponse.json({ error: 'Failed to update routing strategy' }, { status: 500 });
  }
}
