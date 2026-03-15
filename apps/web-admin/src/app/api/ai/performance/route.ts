export const dynamic = 'force-dynamic';

import { NextRequest, NextResponse } from 'next/server';

const GATEWAY_URL = process.env.MCP_GATEWAY_URL ?? 'http://localhost:4444';

function gatewayHeaders(req: NextRequest): HeadersInit {
  const auth = req.headers.get('authorization');
  return auth ? { authorization: auth } : {};
}

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${GATEWAY_URL}/ai/performance`, {
      headers: gatewayHeaders(request),
    });
    if (!response.ok) {
      return NextResponse.json({ error: 'Gateway error' }, { status: response.status });
    }
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to fetch AI performance from gateway:', error);
    return NextResponse.json({ error: 'Failed to fetch AI performance' }, { status: 500 });
  }
}
