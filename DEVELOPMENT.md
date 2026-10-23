# Desenvolvimento e compilação

## Requisitos

- Windows 10 ou 11 para o fluxo do instalador.
- Node.js conforme `app/.nvmrc`.
- npm compatível com o `package-lock.json`.
- Git.
- Inno Setup 6.5.4 ou superior somente quando chegar o momento de compilar o instalador.

## Instalação das dependências

```powershell
cd app
npm ci
cd dashboard
npm ci
cd ..
```

`npm ci` também executa o `postinstall` do projeto, que aplica os patches necessários às bibliotecas do WhatsApp. Não remova `app/scripts/`.

## Configuração local

Crie um `.env` local a partir de `.env.minimal` ou `.env.example`:

```powershell
Copy-Item .env.minimal .env
```

O `.env` é ignorado pelo Git. Não coloque credenciais reais nos arquivos de exemplo.

## Execução durante o desenvolvimento

Backend e painel em modo de desenvolvimento:

```powershell
npm run dev
```

Backend somente:

```powershell
npm run start:dev
```

## Validação

```powershell
npm run format:check
npm run lint
npm test
npm run test:scripts
npm run build:all
```

Consulte `app/package.json` para as demais suítes, incluindo testes E2E, contratos, documentação e engines reais. Testes que usam uma conta real do WhatsApp devem permanecer fora de ambientes compartilhados.

## Build de produção da aplicação

```powershell
cd app
npm ci
cd dashboard
npm ci
cd ..
npm run build:all
```

O backend é gerado em `app/dist/` e o painel em `app/dashboard/dist/`.

## Preparação futura do instalador

Não execute esta etapa durante o desenvolvimento normal. Quando a aplicação estiver revisada e testada:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\Prepare-Payload.ps1
```

Esse script monta `installer/build/payload` usando uma cópia de trabalho, dependências de produção e o Node em uso. Ele não compila o instalador.

Depois, e somente quando houver autorização para gerar o instalador:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\Build-Installer.ps1
```

## Dados do usuário

Em instalações Windows, bancos, sessões, mídia, plugins e chaves geradas ficam sob `app/data/`. O instalador não deve empacotar nem substituir esse diretório em atualizações.

