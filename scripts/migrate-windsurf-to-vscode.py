#!/usr/bin/env python3
"""
Migrador simples de configurações do Windsurf -> VS Code

Funcionalidade:
- Detecta arquivo de configuração do Windsurf (vários locais padrão)
- Extrai listas de extensões e configurações de usuário (settings, keybindings)
- Faz backup das configurações do VS Code e escreve settings/keybindings
- Executa 'code --install-extension' para cada extensão (a menos que --dry-run)

Uso:
  migrate-windsurf-to-vscode.py [--config PATH] [--dry-run]

Observações:
- Suporta macOS e Linux (paths padrão do VS Code). Se o comando 'code' não estiver no PATH,
  o script apenas lista as extensões e dá instruções.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_WINDSURF_PATHS = [
    Path.home() / '.windsurf' / 'mcp.json',
    Path.home() / '.windsurf' / 'settings.json',
    Path.home() / '.codeium' / 'windsurf' / 'mcp_config.json',
]


def detect_vscode_user_dir() -> Path:
    # macOS
    mac = Path.home() / 'Library' / 'Application Support' / 'Code' / 'User'
    linux = Path.home() / '.config' / 'Code' / 'User'
    if mac.exists():
        return mac
    if linux.exists():
        return linux
    # fallback to mac path (create if needed)
    return mac


def load_json(path: Path) -> Any:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def find_windsurf_config(provided: Path | None = None) -> Path | None:
    if provided:
        p = Path(provided).expanduser()
        if p.exists():
            return p
        return None
    for p in DEFAULT_WINDSURF_PATHS:
        if p.exists():
            return p
    return None


def gather_extensions(obj: Any) -> List[str]:
    """Busca recursivamente listas de extensões (heurística simples)."""
    found: List[str] = []

    def walk(x: Any):
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, list) and k.lower().find('ext') >= 0 or k.lower().find('recommend') >= 0:
                    for item in v:
                        if isinstance(item, str):
                            found.append(item)
                else:
                    walk(v)
        elif isinstance(x, list):
            for it in x:
                walk(it)

    walk(obj)
    # dedupe preserving order
    seen = set()
    out = []
    for e in found:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def find_settings(obj: Any) -> Dict[str, Any] | None:
    candidates = ['settings', 'vscodeSettings', 'userSettings', 'editorSettings']
    if isinstance(obj, dict):
        for c in candidates:
            if c in obj and isinstance(obj[c], dict):
                return obj[c]
        # maybe nested
        for v in obj.values():
            res = find_settings(v)
            if res:
                return res
    return None


def find_keybindings(obj: Any) -> Any:
    candidates = ['keybindings', 'keyBindings']
    if isinstance(obj, dict):
        for c in candidates:
            if c in obj:
                return obj[c]
        for v in obj.values():
            res = find_keybindings(v)
            if res:
                return res
    return None


def backup_file(p: Path) -> None:
    if p.exists():
        stamp = datetime.now().strftime('%Y%m%d%H%M%S')
        dest = p.with_name(p.name + '.' + stamp + '.bak')
        shutil.copy2(p, dest)
        print(f'Backup {p} -> {dest}')


def install_extension(ext: str, dry_run: bool) -> bool:
    # Try 'code' in PATH
    code_cmd = shutil.which('code')
    if not code_cmd:
        print("Aviso: comando 'code' não encontrado no PATH. Instalação automática de extensões não será executada.")
        print(f"Extensão sugerida: {ext}")
        return False
    cmd = [code_cmd, '--install-extension', ext]
    print('Executando:', ' '.join(cmd))
    if dry_run:
        return True
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print('Falha ao instalar', ext, e)
        return False


def main() -> int:
    ap = argparse.ArgumentParser(prog='migrate-windsurf-to-vscode')
    ap.add_argument('--config', '-c', help='Path para config do Windsurf (JSON)')
    ap.add_argument('--dry-run', '-n', action='store_true', help='Não faça alterações; apenas mostre o que seria feito')
    args = ap.parse_args()

    cfg_path = find_windsurf_config(Path(args.config).expanduser() if args.config else None)
    if not cfg_path:
        print('Arquivo de configuração do Windsurf não encontrado. Procure em:')
        for p in DEFAULT_WINDSURF_PATHS:
            print(' -', p)
        return 2

    print('Usando config:', cfg_path)
    try:
        cfg = load_json(cfg_path)
    except Exception as e:
        print('Erro ao ler JSON:', e)
        return 3

    exts = gather_extensions(cfg)
    settings = find_settings(cfg)
    keybindings = find_keybindings(cfg)

    user_dir = detect_vscode_user_dir()
    settings_path = user_dir / 'settings.json'
    keybindings_path = user_dir / 'keybindings.json'

    print('\nResumo detectado:')
    print(' - Extensões encontradas:', len(exts))
    print(' - Settings encontrado:', bool(settings))
    print(' - Keybindings encontrado:', bool(keybindings))
    print(' - VS Code User dir:', user_dir)

    if settings:
        print('\nEscrevendo settings para', settings_path)
        if not args.dry_run:
            user_dir.mkdir(parents=True, exist_ok=True)
            backup_file(settings_path)
            with settings_path.open('w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

    if keybindings:
        print('\nEscrevendo keybindings para', keybindings_path)
        if not args.dry_run:
            user_dir.mkdir(parents=True, exist_ok=True)
            backup_file(keybindings_path)
            # keybindings may be a list or dict; write as JSON
            with keybindings_path.open('w', encoding='utf-8') as f:
                json.dump(keybindings, f, indent=2, ensure_ascii=False)

    if exts:
        print('\nInstalando extensões...')
        for e in exts:
            ok = install_extension(e, dry_run=args.dry_run)
            if not ok and not shutil.which('code'):
                # if code missing, skip remaining automatic installs
                print("Interrompendo instalação automática: VS Code CLI não disponível.")
                break

    print('\nConcluído (modo dry-run=' + str(args.dry_run) + ')')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
