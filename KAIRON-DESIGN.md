# KAIRON WA — camada visual sobre o OpenWA

Este pacote preserva o frontend, backend, rotas, APIs, permissões, sessões, webhooks, plugins e demais funcionalidades originais do OpenWA. A alteração realizada é visual e fica concentrada no dashboard.

## Recursos visuais

- `app/dashboard/public/kairon-logo.png`: logotipo, barra lateral e favicon.
- `app/dashboard/public/kairon-login-background.png`: fundo limpo da tela de autenticação.
- `app/dashboard/public/kairon-dashboard-hero.png`: fundo limpo do destaque do painel.
- `app/dashboard/src/pages/Login.tsx` e `Login.css`: composição funcional do login.
- `app/dashboard/src/components/Layout.tsx` e `Layout.css`: marca e navegação interna.
- `app/dashboard/src/App.css`: tokens globais KAIRON usados por todas as páginas.
- `app/dashboard/src/pages/Dashboard.tsx` e `Dashboard.css`: destaque do painel e cartões.

Os textos, campos, botões e menus são componentes HTML/React reais. As imagens são usadas apenas como fundos e marca.

## Desenvolvimento do dashboard

```bash
cd app/dashboard
npm install
npm run dev
```

Compilação e validação:

```bash
npm run build
npm run lint
npm run test:unit
```

Não há chaves de API, sessões reais ou bancos de dados pessoais adicionados por esta personalização. Os arquivos `.env.example` e `.env.minimal` são somente modelos originais de configuração.
