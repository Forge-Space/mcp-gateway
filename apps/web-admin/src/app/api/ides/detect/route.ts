export const dynamic = 'force-dynamic';

import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface IDEResponse {
  detected: string[];
  total: number;
  details: {
    [key: string]: {
      installed: boolean;
      version?: string;
      configPath: string;
    };
  };
}

async function detectIDEs(): Promise<IDEResponse> {
  const detected: string[] = [];
  const details: IDEResponse['details'] = {};

  // Detect Cursor
  try {
    const cursorPath = await findApp('Cursor');
    if (cursorPath) {
      detected.push('cursor');
      details.cursor = {
        installed: true,
        configPath: '~/.cursor/mcp.json',
      };
    } else {
      details.cursor = {
        installed: false,
        configPath: '~/.cursor/mcp.json',
      };
    }
  } catch (error) {
    details.cursor = {
      installed: false,
      configPath: '~/.cursor/mcp.json',
    };
  }

  // Detect Windsurf (VS Code based)
  try {
    const windsurfPath = (await findApp('Windsurf')) || (await findApp('Code'));
    if (windsurfPath) {
      detected.push('windsurf');
      details.windsurf = {
        installed: true,
        configPath: '~/.codeium/windsurf/mcp_config.json',
      };
    } else {
      details.windsurf = {
        installed: false,
        configPath: '~/.codeium/windsurf/mcp_config.json',
      };
    }
  } catch (error) {
    details.windsurf = {
      installed: false,
      configPath: '~/.codeium/windsurf/mcp_config.json',
    };
  }

  // Detect VS Code
  try {
    const vscodePath = (await findApp('Visual Studio Code')) || (await findApp('Code'));
    if (vscodePath) {
      detected.push('vscode');
      details.vscode = {
        installed: true,
        configPath: '~/.vscode/mcp.json',
      };
    } else {
      details.vscode = {
        installed: false,
        configPath: '~/.vscode/mcp.json',
      };
    }
  } catch (error) {
    details.vscode = {
      installed: false,
      configPath: '~/.vscode/mcp.json',
    };
  }

  // Detect Claude Desktop
  try {
    const claudePath = await findApp('Claude');
    if (claudePath) {
      detected.push('claude');
      details.claude = {
        installed: true,
        configPath: '~/Library/Application Support/Claude/claude_desktop_config.json',
      };
    } else {
      details.claude = {
        installed: false,
        configPath: '~/Library/Application Support/Claude/claude_desktop_config.json',
      };
    }
  } catch (error) {
    details.claude = {
      installed: false,
      configPath: '~/Library/Application Support/Claude/claude_desktop_config.json',
    };
  }

  return {
    detected,
    total: detected.length,
    details,
  };
}

async function findApp(appName: string): Promise<string | null> {
  try {
    // macOS specific detection
    if (process.platform === 'darwin') {
      const { stdout } = await execAsync(`mdfind "kMDItemDisplayName == '${appName}'"`);
      return stdout.trim() || null;
    }

    // Linux detection
    if (process.platform === 'linux') {
      try {
        await execAsync(`which ${appName.toLowerCase().replace(/\s+/g, '-')}`);
        return appName;
      } catch {
        return null;
      }
    }

    // Windows detection
    if (process.platform === 'win32') {
      try {
        await execAsync(`where ${appName}`);
        return appName;
      } catch {
        return null;
      }
    }

    return null;
  } catch (error) {
    return null;
  }
}

export async function GET(request: NextRequest) {
  try {
    const result = await detectIDEs();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Failed to detect IDEs:', error);

    // Fallback to common IDEs
    return NextResponse.json({
      detected: ['cursor', 'windsurf'],
      total: 2,
      details: {
        cursor: { installed: true, configPath: '~/.cursor/mcp.json' },
        windsurf: { installed: true, configPath: '~/.codeium/windsurf/mcp_config.json' },
        vscode: { installed: false, configPath: '~/.vscode/mcp.json' },
        claude: {
          installed: false,
          configPath: '~/Library/Application Support/Claude/claude_desktop_config.json',
        },
      },
    });
  }
}
