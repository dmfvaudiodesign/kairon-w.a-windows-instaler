# KAIRON WA — pacote de código-fonte

Este pacote reúne o código-fonte do KAIRON WA para desenvolvimento, revisão e futura publicação em um repositório privado.

## Estrutura

- `app/`: backend NestJS, frontend/painel Vite, SDKs, testes, scripts e patches do WhatsApp.
- `installer/`: código-fonte editável do instalador Windows, scripts auxiliares e referências visuais.
- `DEVELOPMENT.md`: preparação do ambiente, execução, testes e compilação.
- `SECURITY-AND-DATA.md`: dados excluídos e cuidados antes de publicar.

## O que não está incluído

Por segurança e por prática normal de versionamento, o pacote não contém:

- `node_modules/`;
- builds `dist/`;
- `.env` local;
- chaves de API;
- sessões reais do WhatsApp;
- bancos SQLite;
- mídia, logs, caches ou dados pessoais;
- executável ou instalador compilado.

As versões exatas das dependências estão registradas em `app/package-lock.json` e
`app/dashboard/package-lock.json`. Use `npm ci` para reproduzi-las.

## Início rápido

Consulte `DEVELOPMENT.md`. Em resumo:

```powershell
cd app
npm ci
cd dashboard
npm ci
cd ..
Copy-Item .env.minimal .env
npm run dev
```

Revise o `.env` local antes de iniciar. Nunca envie esse arquivo ao GitHub.

