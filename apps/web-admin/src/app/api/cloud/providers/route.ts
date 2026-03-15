export const dynamic = 'force-dynamic';

import { NextRequest, NextResponse } from 'next/server';

const GATEWAY_URL = process.env.MCP_GATEWAY_URL ?? 'http://localhost:4444';

function gatewayHeaders(req: NextRequest): HeadersInit {
  const auth = req.headers.get('authorization');
  return auth ? { authorization: auth } : {};
}

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${GATEWAY_URL}/cloud/providers`, {
      headers: gatewayHeaders(request),
    });
    if (!response.ok) {
      return NextResponse.json({ error: 'Gateway error' }, { status: response.status });
    }
    return NextResponse.json(await response.json());
  } catch (error) {
    console.error('Failed to fetch cloud providers from gateway:', error);
    return NextResponse.json({ error: 'Failed to fetch cloud providers' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const response = await fetch(`${GATEWAY_URL}/cloud/providers`, {
      method: 'POST',
      headers: { ...gatewayHeaders(request), 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      return NextResponse.json({ error: 'Gateway error' }, { status: response.status });
    }
    return NextResponse.json(await response.json(), { status: 201 });
  } catch (error) {
    console.error('Failed to register cloud provider:', error);
    return NextResponse.json({ error: 'Failed to register cloud provider' }, { status: 500 });
  }
}
