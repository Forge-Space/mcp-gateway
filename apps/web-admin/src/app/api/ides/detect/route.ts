export const dynamic = 'force-dynamic';

import { NextRequest, NextResponse } from 'next/server';

const GATEWAY_URL = process.env.MCP_GATEWAY_URL ?? 'http://localhost:4444';

function gatewayHeaders(req: NextRequest): HeadersInit {
  const auth = req.headers.get('authorization');
  return auth ? { authorization: auth } : {};
}

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${GATEWAY_URL}/ide/detect`, {
      headers: gatewayHeaders(request),
    });
    if (!response.ok) {
      return NextResponse.json({ error: 'Gateway error' }, { status: response.status });
    }
    // Normalise to the shape the IDE integration page already expects:
    // { detected: string[], total: number, details: { [id]: { installed, configPath } } }
    const data = (await response.json()) as {
      system: string;
      detected: Array<{ id: string; name: string; detected: boolean; config_path: string | null }>;
    };
    const details: Record<string, { installed: boolean; configPath: string | null }> = {};
    const detectedIds: string[] = [];
    for (const ide of data.detected) {
      details[ide.id] = { installed: ide.detected, configPath: ide.config_path };
      if (ide.detected) detectedIds.push(ide.id);
    }
    return NextResponse.json({ detected: detectedIds, total: detectedIds.length, details });
  } catch (error) {
    console.error('Failed to detect IDEs from gateway:', error);
    return NextResponse.json({ error: 'Failed to detect IDEs' }, { status: 500 });
  }
}
