# Código-fonte do instalador Windows

Esta pasta contém uma reconstrução editável do instalador que acompanha o pacote. O código-fonte temporário usado na compilação anterior não estava mais disponível; os scripts VBS e o ícone em `payload/` foram recuperados do instalador existente, e o manifesto Inno Setup foi reconstruído com o mesmo destino, porta e forma de inicialização.

Nenhum executável compilado faz parte deste pacote.

## Arquivos

- `KAIRON-WA.iss`: manifesto Inno Setup.
- `DESIGN.md`: referência visual e decisões de implementação.
- `Prepare-Payload.ps1`: cria uma cópia de trabalho, compila aplicação/painel e monta o payload.
- `Build-Installer.ps1`: valida o payload e chama o Inno Setup 6.
- `tools/render_ui.py`: gera as telas do instalador já compostas (`assets/ui/*.bmp`).
- `tools/fonts/`: fontes livres (Inter e Montserrat, licença OFL) usadas pelo gerador.
- `payload/*.vbs`: iniciar, parar e mostrar a chave local.
- `config/windows.env.example`: configuração de produção sem segredos.
- `assets/reference/`: referências visuais fornecidas para a interface final.

O diretório `build/` é gerado localmente e deve permanecer fora do Git.

O interior personalizado do instalador é criado no bloco `[Code]` de `KAIRON-WA.iss`.

Cada tela (boas-vindas, instalação e conclusão) é uma imagem já composta com fundo, logo, textos e botões. Por cima dela o script coloca apenas controles sem janela própria (`TBitmapImage` e `TLabel` transparente): a barra de progresso, a porcentagem real, os marcadores das etapas e as áreas clicáveis dos botões. Veja `DESIGN.md` para o motivo.

## Alterar textos ou layout das telas

1. Edite `tools/render_ui.py` (textos, posições, cores).
2. Rode `python3 installer/tools/render_ui.py` (requer `pip install pillow`).
3. Se mudar a posição da barra, das etapas ou dos botões, atualize as constantes correspondentes no `[Code]` de `KAIRON-WA.iss` (os números são os mesmos nos dois arquivos).
4. Faça commit de `assets/ui/*.bmp` junto — o GitHub Actions não precisa de Python.

