# Migrar configurações do Windsurf para VS Code

Este utilitário ajuda a importar configurações do Windsurf (settings, keybindings e extensões) para o VS Code.

PASSOS RÁPIDOS

1. Detecta automaticamente os arquivos de config do Windsurf (ex.: `~/.windsurf/mcp.json`, `~/.codeium/windsurf/mcp_config.json`).
2. Faz backup dos arquivos existentes do VS Code (`settings.json`, `keybindings.json`).
3. Escreve `settings.json` e `keybindings.json` no diretório de usuário do VS Code.
4. Tenta instalar extensões via o CLI do VS Code (`code --install-extension`).

USO (fish shell)

```fish
# modo apenas simulação (recomendado primeiro)
scripts/migrate-windsurf-to-vscode.fish --dry-run

# executar a migração (pode pedir permissão para instalar extensões)
scripts/migrate-windsurf-to-vscode.fish
```

OPÇÕES

- `--config PATH` : usar um arquivo Windsurf específico.
- `--dry-run` : imprime o que seria feito sem aplicar alterações.

NOTAS E RESOLUÇÃO DE PROBLEMAS

- Se o comando `code` não existir no PATH, o script apenas listará as extensões encontradas e fará o backup/escrita de settings/keybindings (dependendo do modo). Para habilitar o `code` no PATH no macOS abra o VS Code e selecione "Command Palette" -> "Shell Command: Install 'code' command in PATH".
- O script tenta detectar o diretório de usuário do VS Code (`~/Library/Application Support/Code/User` no macOS ou `~/.config/Code/User` no Linux). Se você usa uma build diferente (Insiders, OSS), copie manualmente os arquivos gerados.

FALLBACK MANUAL

1. Abra o arquivo de config do Windsurf e copie o bloco `settings` para `settings.json` do VS Code.
2. Copie `keybindings` para `keybindings.json` do VS Code.
3. Instale extensões manualmente com:

```fish
code --install-extension publisher.extension
```

CONTATO

Se quiser que eu ajuste o script para um formato de Windsurf específico, cole aqui um trecho (remova segredos) e eu adapto a extração automaticamente.
