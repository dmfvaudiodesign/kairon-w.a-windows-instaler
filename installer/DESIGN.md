# Especificação visual do instalador

A referência oficial são as imagens em `assets/reference/` (telas de boas-vindas, instalação e conclusão).

## Por que as telas são imagens compostas

A primeira versão montava a interface com `TNewStaticText` e `TPanel` por cima de um fundo. No Windows isso não funciona:

| Sintoma no instalador compilado | Causa |
| --- | --- |
| Caixa preta atrás de cada texto | `TNewStaticText` é um controle com janela própria e pinta um fundo sólido; não existe transparência. |
| Quadrado magenta atrás do logo e dos ícones | BMP de 24 bits não tem canal alfa; o magenta era uma "cor-chave" que nunca era removida. |
| Botão "Avançar" invisível e barra de progresso vazia | Com o tema do Windows ativo, `TPanel` herda o fundo do formulário (preto) e ignora `Color`. O texto preto do botão ficava sobre preto. |
| Botão "Cancel" em inglês aparecendo na instalação | Faltava a seção `[Languages]` e o botão nativo voltava a ficar visível na página de instalação. |

## Como funciona agora

- `tools/render_ui.py` (Python + Pillow) compõe cada tela inteira: fundo, logo PNG com transparência real, textos, ícones, cartões e botões.
- Gera versões para 100%, 125%, 150% e 200% de escala do Windows, para ficar nítido em qualquer monitor (175% usa a versão de 150%).
- O `[Code]` do `.iss` exibe a tela num `TBitmapImage` e sobrepõe apenas controles sem janela (desenhados direto sobre o fundo):
  - barra de progresso: recorte da própria tela com a barra cheia, revelado conforme o progresso real;
  - porcentagem: `TLabel` com `Transparent := True`;
  - etapas: recortes "pendente", "ativo" e "concluído" de cada marcador;
  - botões: `TLabel` transparente e clicável sobre o botão desenhado.
- Os botões nativos do Inno Setup continuam ativos, só que fora da área visível: Enter avança, Esc cancela e o "X" da janela pede confirmação normalmente.
- Se aparecer alguma página inesperada (por exemplo "Preparando para instalar"), o script mostra a interface nativa do Inno Setup para não travar o usuário.

## Telas

1. Boas-vindas: marca à esquerda, divisor vertical, título e benefícios à direita, botões Cancelar e Avançar.
2. Instalação: marca central, progresso real, porcentagem real, quatro etapas e Cancelar.
3. Conclusão: marca, confirmação, mensagem final e botão Concluir.

## Ativos

- `assets/backgrounds/*.png`: fundos mestre (sem texto) e o logotipo `kairon-logo.png` (com transparência).
- `assets/ui/*.bmp`: telas e recortes gerados por `tools/render_ui.py`; são os arquivos embutidos no instalador.
- `tools/fonts/`: Inter e Montserrat (SIL Open Font License).
- `assets/reference/`: referências visuais.

## Compilação

Inno Setup 6.4 ou superior. O script foi compilado e executado com sucesso (Inno Setup 6.4.1) para validar a interface.
