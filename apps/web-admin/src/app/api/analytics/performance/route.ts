export const dynamic = 'force-dynamic';

import { NextRequest, NextResponse } from 'next/server';

const GATEWAY_URL = process.env.MCP_GATEWAY_URL ?? 'http://localhost:4444';

function gatewayHeaders(req: NextRequest): HeadersInit {
  const auth = req.headers.get('authorization');
  return auth ? { authorization: auth } : {};
}

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const period = url.searchParams.get('period') ?? '24h';

    const response = await fetch(
      `${GATEWAY_URL}/monitoring/performance?period=${encodeURIComponent(period)}`,
      { headers: gatewayHeaders(request) }
    );
    if (!response.ok) {
      return NextResponse.json({ error: 'Gateway error' }, { status: response.status });
    }
    return NextResponse.json(await response.json());
  } catch (error) {
    console.error('Failed to fetch analytics performance from gateway:', error);
    return NextResponse.json({ error: 'Failed to fetch analytics performance' }, { status: 500 });
  }
}
