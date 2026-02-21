import { spawn } from 'child_process';
import { createWriteStream } from 'fs';

const out = createWriteStream('/Users/lucassantana/Desenvolvimento/mcp-gateway/apps/web-admin/build-result.txt');

const proc = spawn('npm', ['run', 'build'], {
  cwd: '/Users/lucassantana/Desenvolvimento/mcp-gateway/apps/web-admin',
  env: { ...process.env, FORCE_COLOR: '0' },
});

proc.stdout.on('data', d => { out.write(d); process.stdout.write(d); });
proc.stderr.on('data', d => { out.write(d); process.stderr.write(d); });
proc.on('close', code => {
  out.write(`\nEXIT: ${code}\n`);
  out.end();
  process.exit(code);
});
