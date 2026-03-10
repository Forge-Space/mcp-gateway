import { spawn } from 'child_process';
import { createWriteStream } from 'fs';
import { createRequire } from 'module';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const require = createRequire(import.meta.url);
const npmCliPath = require.resolve('npm/bin/npm-cli.js');
const currentDir = dirname(fileURLToPath(import.meta.url));
const out = createWriteStream(resolve(currentDir, 'build-result.txt'));

const proc = spawn(process.execPath, [npmCliPath, 'run', 'build'], {
  cwd: currentDir,
});

proc.stdout.on('data', d => { out.write(d); process.stdout.write(d); });
proc.stderr.on('data', d => { out.write(d); process.stderr.write(d); });
proc.on('close', code => {
  out.write(`\nEXIT: ${code}\n`);
  out.end();
  process.exit(code);
});
