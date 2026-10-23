# Segurança e dados

## Exclusões aplicadas ao pacote

- `.env` local;
- `data/` e `dashboard/dist/`;
- `node_modules/`;
- bancos `*.db`, `*.sqlite` e `*.sqlite3`;
- logs, backups, caches e arquivos temporários;
- chaves e sessões geradas em execução.

## Antes de publicar no GitHub

1. Use um repositório privado.
2. Confirme que `.env`, `data/`, `node_modules/` e builds continuam ignorados.
3. Rode uma ferramenta de detecção de segredos no histórico antes do primeiro push.
4. Não copie dados de uma instalação existente para este repositório.
5. Use GitHub Secrets ou um cofre de segredos para CI/CD.

Arquivos `.env.example` e `.env.minimal` são modelos de configuração e devem conter apenas valores de exemplo.

