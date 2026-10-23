#!/usr/bin/env python3
"""
Gera as telas do instalador KAIRON WA já compostas (fundo + logo + textos + botões).

Por que compor tudo em imagem?
  Os controles de janela do Inno Setup (TNewStaticText, TPanel) NÃO são transparentes:
  cada um pinta um retângulo sólido por cima do fundo (as "caixas pretas"), o TPanel
  ignora a cor quando o tema do Windows está ativo (botão "Avançar" e barra de
  progresso pretos) e BMP não tem canal alfa (o quadrado magenta do logo).
  Compondo cada tela aqui, o Inno Setup só precisa exibir UMA imagem de fundo e
  sobrepor poucas peças dinâmicas (barra, etapas, porcentagem), que também são
  recortes exatos destas mesmas imagens — então tudo encaixa pixel a pixel.

Uso:  python3 installer/tools/render_ui.py
Requer: Pillow (pip install pillow)
Saída: installer/assets/ui/*.bmp  (uma versão por escala de DPI do Windows)

As coordenadas abaixo são lógicas (janela de 960 x 640). O script .iss usa a mesma
fórmula de arredondamento: S(v) = (v * P + 50) div 100, com P = escala em %.
"""
from __future__ import annotations

import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
BACKGROUNDS = os.path.join(ASSETS, "backgrounds")
OUT = os.path.join(ASSETS, "ui")
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

SCALES = [100, 125, 150, 200]
W, H = 960, 640
SS = 2  # supersampling para bordas suaves

# Paleta
GREEN = (46, 240, 150)
GREEN_LIGHT = (120, 255, 190)
GREEN_DEEP = (10, 200, 110)
WHITE = (255, 255, 255)
MUTED = (196, 208, 202)
DIM = (120, 140, 130)

# ---------------------------------------------------------------- layout (lógico)
# Tela de instalação: itens dinâmicos (o .iss usa EXATAMENTE os mesmos números)
PROGRESS_BOX = (150, 340, 790, 362)           # x1, y1, x2, y2 da trilha
STAGE_CARD = (130, 392, 830, 512)
STAGE_COLS = [(130 + i * 175, 130 + (i + 1) * 175) for i in range(4)]
STAGE_MARK_R = 10
STAGE_MARK_Y = 486
STAGE_MARK_BOX = 15                            # meia-largura do recorte do marcador


def S(v: int, p: int) -> int:
    """Mesmo arredondamento usado no Pascal Script."""
    return (v * p + 50) // 100


def stage_mark_cx(i: int) -> int:
    x1, _ = STAGE_COLS[i]
    return x1 + 42


# ---------------------------------------------------------------- fontes
def font(name: str, size: float, weight: int | None = None) -> ImageFont.FreeTypeFont:
    files = {
        "inter": "Inter-Regular.otf",
        "inter-medium": "Inter-Medium.otf",
        "inter-semibold": "Inter-SemiBold.otf",
        "inter-bold": "Inter-Bold.otf",
        "brand": "Montserrat-Variable.ttf",
    }
    f = ImageFont.truetype(os.path.join(FONTS, files[name]), max(1, int(round(size))))
    if weight is not None:
        f.set_variation_by_axes([weight])
    return f


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, scale_pct: int):
        self.p = scale_pct
        self.k = scale_pct / 100 * SS
        self.size = (int(round(W * self.k)), int(round(H * self.k)))
        self.img = Image.new("RGBA", self.size, (0, 0, 0, 255))

    def px(self, v: float) -> int:
        return int(round(v * self.k))

    def box(self, b):
        return tuple(self.px(v) for v in b)

    def layer(self):
        return Image.new("RGBA", self.size, (0, 0, 0, 0))

    def put(self, layer, blur: float = 0):
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(blur * self.k))
        self.img.alpha_composite(layer)

    # ---- fundo
    def background(self, filename: str, darken: float = 0.0):
        bg = Image.open(os.path.join(BACKGROUNDS, filename)).convert("RGB")
        tw, th = self.size
        r = max(tw / bg.width, th / bg.height)
        bg = bg.resize((math.ceil(bg.width * r), math.ceil(bg.height * r)), Image.LANCZOS)
        left, top = (bg.width - tw) // 2, (bg.height - th) // 2
        bg = bg.crop((left, top, left + tw, top + th)).convert("RGBA")
        self.img = bg
        if darken:
            self.put(Image.new("RGBA", self.size, (0, 0, 0, int(255 * darken))))

    def gradient_overlay(self, x1, x2, a1, a2, color=(0, 0, 0), y1=0, y2=H, horizontal=True):
        """Faixa com transparência em degradê (linear) entre a1 e a2."""
        lay = self.layer()
        d = ImageDraw.Draw(lay)
        if horizontal:
            X1, X2 = self.px(x1), self.px(x2)
            for x in range(X1, X2):
                t = (x - X1) / max(1, X2 - X1 - 1)
                d.line([(x, self.px(y1)), (x, self.px(y2))], fill=color + (int(255 * (a1 + (a2 - a1) * t)),))
        else:
            Y1, Y2 = self.px(y1), self.px(y2)
            for y in range(Y1, Y2):
                t = (y - Y1) / max(1, Y2 - Y1 - 1)
                d.line([(self.px(x1), y), (self.px(x2), y)], fill=color + (int(255 * (a1 + (a2 - a1) * t)),))
        self.put(lay)

    def radial_glow(self, cx, cy, rx, ry, color, alpha, blur):
        lay = self.layer()
        d = ImageDraw.Draw(lay)
        d.ellipse(self.box((cx - rx, cy - ry, cx + rx, cy + ry)), fill=color + (int(255 * alpha),))
        self.put(lay, blur)

    # ---- logo
    def logo(self, cx, cy, size, glow=True):
        lg = Image.open(os.path.join(BACKGROUNDS, "kairon-logo.png")).convert("RGBA")
        s = self.px(size)
        lg = lg.resize((s, s), Image.LANCZOS)
        if glow:
            self.radial_glow(cx, cy, size * 0.42, size * 0.42, (20, 230, 120), 0.30, size * 0.12)
        self.img.alpha_composite(lg, (self.px(cx - size / 2), self.px(cy - size / 2)))

    # ---- texto
    def _mask(self, text, f, tracking=0.0):
        """Máscara 'L' do texto (com espaçamento opcional) e sua largura."""
        if not tracking:
            l, t, r, b = f.getbbox(text)
            asc, desc = f.getmetrics()
            m = Image.new("L", (int(r) + 4, asc + desc + 4), 0)
            ImageDraw.Draw(m).text((0, 0), text, font=f, fill=255)
            return m, f.getlength(text)
        tr = tracking * self.k
        width = sum(f.getlength(c) for c in text) + tr * (len(text) - 1)
        asc, desc = f.getmetrics()
        m = Image.new("L", (int(width) + 8, asc + desc + 4), 0)
        d = ImageDraw.Draw(m)
        x = 0.0
        for c in text:
            d.text((x, 0), c, font=f, fill=255)
            x += f.getlength(c) + tr
        return m, width

    def text_width(self, text, fname, size, weight=None, tracking=0.0):
        f = font(fname, size * self.k, weight)
        _, w = self._mask(text, f, tracking)
        return w / self.k

    def text(self, x, y, text, fname, size, fill=WHITE, weight=None, align="left",
             tracking=0.0, gradient=None, shadow=True, glow=None):
        """
        y = topo da caixa da fonte (ascendente). gradient = [(pos, (r,g,b)), ...] vertical.
        glow = (cor, alpha, raio) para brilho externo.
        """
        f = font(fname, size * self.k, weight)
        m, w = self._mask(text, f, tracking)
        X = self.px(x)
        if align == "center":
            X = int(round(self.px(x) - w / 2))
        elif align == "right":
            X = int(round(self.px(x) - w))
        Y = self.px(y)

        if glow:
            gc, ga, gr = glow
            lay = self.layer()
            col = Image.new("RGBA", m.size, gc + (0,))
            col.putalpha(m.point(lambda v: int(v * ga)))
            lay.alpha_composite(col, (X, Y))
            self.put(lay, gr)
        if shadow:
            lay = self.layer()
            col = Image.new("RGBA", m.size, (0, 0, 0, 0))
            col.putalpha(m.point(lambda v: int(v * 0.65)))
            lay.alpha_composite(col, (X, Y + max(1, self.px(1.5))))
            self.put(lay, 1.6)

        if gradient:
            fillimg = Image.new("RGBA", m.size)
            gd = ImageDraw.Draw(fillimg)
            capt = f.getbbox("H")[1]
            caph = f.getbbox("H")[3] - capt
            for yy in range(m.size[1]):
                t = min(1, max(0, (yy - capt) / max(1, caph)))
                c = _grad(gradient, t)
                gd.line([(0, yy), (m.size[0], yy)], fill=c + (255,))
            fillimg.putalpha(m)
        else:
            fillimg = Image.new("RGBA", m.size, fill + (255,))
            fillimg.putalpha(m)
        self.img.alpha_composite(fillimg, (X, Y))
        return w / self.k

    # ---- formas
    def rrect(self, b, r, fill=None, outline=None, width=1.0, blur=0):
        lay = self.layer()
        d = ImageDraw.Draw(lay)
        d.rounded_rectangle(self.box(b), radius=self.px(r), fill=fill,
                            outline=outline, width=max(1, self.px(width)) if outline else 0)
        self.put(lay, blur)

    def rrect_gradient(self, b, r, top, bottom, alpha=255):
        x1, y1, x2, y2 = self.box(b)
        g = Image.new("RGBA", (x2 - x1, y2 - y1))
        gd = ImageDraw.Draw(g)
        for yy in range(y2 - y1):
            t = yy / max(1, y2 - y1 - 1)
            c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            gd.line([(0, yy), (x2 - x1, yy)], fill=c + (alpha,))
        mask = Image.new("L", g.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, g.size[0] - 1, g.size[1] - 1), radius=self.px(r), fill=255)
        g.putalpha(Image.eval(mask, lambda v: v * alpha // 255))
        self.img.alpha_composite(g, (x1, y1))

    def line(self, pts, color, width, blur=0):
        lay = self.layer()
        d = ImageDraw.Draw(lay)
        P = [(self.px(x), self.px(y)) for x, y in pts]
        w = max(1, self.px(width))
        d.line(P, fill=color, width=w, joint="curve")
        for x, y in P:  # pontas arredondadas
            d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=color)
        self.put(lay, blur)

    def arc(self, b, start, end, color, width, blur=0):
        lay = self.layer()
        ImageDraw.Draw(lay).arc(self.box(b), start, end, fill=color, width=max(1, self.px(width)))
        self.put(lay, blur)

    def ellipse(self, b, fill=None, outline=None, width=1.0, blur=0):
        lay = self.layer()
        ImageDraw.Draw(lay).ellipse(self.box(b), fill=fill, outline=outline,
                                    width=max(1, self.px(width)) if outline else 0)
        self.put(lay, blur)

    def polygon(self, pts, fill=None, outline=None, width=1.0):
        lay = self.layer()
        d = ImageDraw.Draw(lay)
        P = [(self.px(x), self.px(y)) for x, y in pts]
        if fill:
            d.polygon(P, fill=fill)
        if outline:
            self.line(pts + [pts[0]], outline, width)
        self.put(lay)

    def vline_glow(self, x, y1, y2, color, peak=0.8):
        """Linha vertical que some nas pontas, com brilho."""
        for blur, wdt, k in ((6, 6, 0.35), (0, 1.4, 1.0)):
            lay = self.layer()
            d = ImageDraw.Draw(lay)
            Y1, Y2 = self.px(y1), self.px(y2)
            for yy in range(Y1, Y2):
                t = (yy - Y1) / max(1, Y2 - Y1)
                a = math.sin(math.pi * t) ** 1.4 * peak * k
                d.line([(self.px(x - wdt / 2), yy), (self.px(x + wdt / 2), yy)], fill=color + (int(255 * a),))
            self.put(lay, blur)

    def hline_fade(self, x1, x2, y, color, peak=0.5, width=1.0):
        lay = self.layer()
        d = ImageDraw.Draw(lay)
        X1, X2 = self.px(x1), self.px(x2)
        for xx in range(X1, X2):
            t = (xx - X1) / max(1, X2 - X1)
            a = math.sin(math.pi * t) ** 0.8 * peak
            d.line([(xx, self.px(y)), (xx, self.px(y + width))], fill=color + (int(255 * a),))
        self.put(lay)

    def final(self) -> Image.Image:
        out = (int(round(W * self.p / 100)), int(round(H * self.p / 100)))
        return self.img.resize(out, Image.LANCZOS).convert("RGB")


def _grad(stops, t):
    for (p1, c1), (p2, c2) in zip(stops, stops[1:]):
        if t <= p2:
            u = (t - p1) / max(1e-6, p2 - p1)
            return tuple(int(c1[i] + (c2[i] - c1[i]) * u) for i in range(3))
    return stops[-1][1]


METAL = [(0.0, (255, 255, 255)), (0.45, (236, 240, 238)), (0.62, (150, 160, 156)), (1.0, (228, 232, 230))]
GREEN_TXT = [(0.0, (150, 255, 200)), (0.5, (40, 236, 140)), (1.0, (12, 196, 104))]


# ---------------------------------------------------------------- ícones de linha
def icon_chat(c: Canvas, x, y, s, color=GREEN, w=2.2):
    cx, cy, r = x + s * 0.52, y + s * 0.47, s * 0.40
    c.arc((cx - r, cy - r, cx + r, cy + r), 135, 110 + 360, color, w)
    c.line([(cx - r * 0.72, cy + r * 0.70), (x + s * 0.08, y + s * 0.95), (cx - r * 0.25, cy + r * 0.97)], color, w)
    for i in (-1, 0, 1):
        dx = cx + i * r * 0.42
        c.ellipse((dx - s * 0.05, cy - s * 0.05, dx + s * 0.05, cy + s * 0.05), fill=color + (255,))


def icon_gear(c: Canvas, x, y, s, color=GREEN, w=2.2):
    cx, cy = x + s / 2, y + s / 2
    teeth = 8
    pts = []
    ro, ri = s * 0.47, s * 0.36
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4) - math.pi / 2
        rr = ro if (i % 4) in (1, 2) else ri
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    c.line(pts + [pts[0]], color, w)
    r = s * 0.14
    c.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color + (255,), width=w)


def icon_shield(c: Canvas, x, y, s, color=GREEN, w=2.2):
    pts = [(x + s * 0.5, y + s * 0.04), (x + s * 0.88, y + s * 0.18), (x + s * 0.86, y + s * 0.52),
           (x + s * 0.5, y + s * 0.96), (x + s * 0.14, y + s * 0.52), (x + s * 0.12, y + s * 0.18)]
    c.line(pts + [pts[0]], color, w)
    c.line([(x + s * 0.33, y + s * 0.50), (x + s * 0.46, y + s * 0.63), (x + s * 0.69, y + s * 0.38)], color, w)


def icon_file(c: Canvas, x, y, s, color=GREEN, w=2.2):
    pts = [(x + s * 0.18, y + s * 0.04), (x + s * 0.62, y + s * 0.04), (x + s * 0.84, y + s * 0.26),
           (x + s * 0.84, y + s * 0.96), (x + s * 0.18, y + s * 0.96)]
    c.line(pts + [pts[0]], color, w)
    c.line([(x + s * 0.60, y + s * 0.05), (x + s * 0.60, y + s * 0.28), (x + s * 0.83, y + s * 0.28)], color, w)
    c.line([(x + s * 0.33, y + s * 0.56), (x + s * 0.68, y + s * 0.56)], color, w)
    c.line([(x + s * 0.33, y + s * 0.74), (x + s * 0.58, y + s * 0.74)], color, w)


def icon_database(c: Canvas, x, y, s, color=GREEN, w=2.2):
    l, r = x + s * 0.12, x + s * 0.88
    eh = s * 0.24
    c.ellipse((l, y + s * 0.04, r, y + s * 0.04 + eh), outline=color + (255,), width=w)
    for yy in (0.40, 0.70):
        c.arc((l, y + s * yy - eh / 2 + s * 0.04, r, y + s * yy + eh / 2 + s * 0.04), 0, 180, color, w)
    c.arc((l, y + s * 0.96 - eh, r, y + s * 0.96), 0, 180, color, w)
    c.line([(l, y + s * 0.16), (l, y + s * 0.84)], color, w)
    c.line([(r, y + s * 0.16), (r, y + s * 0.84)], color, w)


# ---------------------------------------------------------------- peças comuns
def brand(c: Canvas, cx, y, size, center=True):
    """'KAIRON' metálico + 'WA' verde."""
    gap = size * 0.32
    wk = c.text_width("KAIRON", "brand", size, 800, tracking=size * 0.02)
    ww = c.text_width("WA", "brand", size, 800, tracking=size * 0.02)
    x = cx - (wk + gap + ww) / 2 if center else cx
    c.text(x, y, "KAIRON", "brand", size, weight=800, tracking=size * 0.02, gradient=METAL)
    c.text(x + wk + gap, y, "WA", "brand", size, weight=800, tracking=size * 0.02, gradient=GREEN_TXT,
           glow=(GREEN, 0.45, size * 0.18))


def button_secondary(c: Canvas, b, label):
    x1, y1, x2, y2 = b
    c.rrect(b, 9, fill=(6, 12, 10, 225), outline=(170, 190, 182, 120), width=1.2)
    c.text((x1 + x2) / 2, y1 + (y2 - y1) / 2 - 11.5, label, "inter-medium", 17, align="center", shadow=False)


def button_primary(c: Canvas, b, label):
    x1, y1, x2, y2 = b
    c.rrect((x1 - 2, y1 - 2, x2 + 2, y2 + 2), 11, fill=GREEN + (150,), blur=9)
    c.rrect_gradient(b, 9, (98, 255, 178), (18, 214, 116))
    c.rrect(b, 9, outline=(190, 255, 220, 200), width=1.2)
    c.hline_fade(x1 + 10, x2 - 10, y1 + 2, (255, 255, 255), 0.55)
    c.text((x1 + x2) / 2, y1 + (y2 - y1) / 2 - 11.5, label, "inter-bold", 17, fill=(4, 34, 18),
           align="center", shadow=False)


# ---------------------------------------------------------------- telas
WELCOME_NEXT = (770, 566, 932, 618)
WELCOME_CANCEL = (590, 566, 752, 618)
INSTALL_CANCEL = (770, 566, 932, 618)
FINISH_BUTTON = (308, 470, 652, 530)


def render_welcome(p):
    c = Canvas(p)
    c.background("welcome.png", darken=0.18)
    c.gradient_overlay(470, 640, 0.0, 0.55)
    c.gradient_overlay(640, 960, 0.55, 0.62)
    c.gradient_overlay(0, 960, 0.0, 0.55, y1=520, y2=640, horizontal=False)

    # Lado esquerdo: marca
    c.radial_glow(250, 300, 230, 120, (10, 120, 60), 0.35, 60)
    c.logo(250, 250, 350)
    brand(c, 250, 444, 44)

    # Divisor
    c.vline_glow(500, 52, 510, (90, 255, 170), 0.75)

    # Lado direito: textos
    x = 548
    c.text(x, 72, "Bem-vindo ao", "inter-bold", 33)
    c.text(x, 114, "Instalador do", "inter-bold", 33)
    brand(c, x, 160, 50, center=False)
    c.text(x, 244, "Este assistente irá instalar o KAIRON WA", "inter", 16, fill=MUTED)
    c.text(x, 267, "em seu computador.", "inter", 16, fill=MUTED)
    c.text(x, 304, "Uma solução de comunicação mais inteligente,", "inter", 16, fill=MUTED)
    c.text(x, 327, "rápida e totalmente personalizada.", "inter", 16, fill=MUTED)

    feats = [(icon_chat, "Atendimento via WhatsApp"), (icon_gear, "Integração com IA"),
             (icon_shield, "Seguro e fácil de usar")]
    for i, (ico, label) in enumerate(feats):
        yy = 384 + i * 48
        ico(c, x, yy, 28)
        c.text(x + 46, yy + 4, label, "inter-medium", 16.5)

    # Barra inferior e botões
    c.hline_fade(30, 930, 540, (90, 255, 170), 0.28)
    button_secondary(c, WELCOME_CANCEL, "Cancelar")
    button_primary(c, WELCOME_NEXT, "Avançar  >")
    return c.final()


def _stage_marker(c: Canvas, cx, cy, state):
    r = STAGE_MARK_R
    if state == "pending":
        c.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(110, 130, 122, 220), width=1.6)
    elif state == "active":
        c.ellipse((cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3), fill=GREEN + (70,), blur=4)
        for k in range(8):
            a0 = k * 45 + 8
            c.arc((cx - r, cy - r, cx + r, cy + r), a0, a0 + 24, GREEN + (255,), 2.6)
    else:  # done
        c.ellipse((cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3), fill=GREEN + (90,), blur=4)
        c.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GREEN + (255,))
        c.line([(cx - 4.6, cy + 0.2), (cx - 1.2, cy + 3.6), (cx + 5, cy - 3.4)], (4, 40, 20, 255), 2.4)


def render_installing(p, bar_full=False, mark_state="pending"):
    c = Canvas(p)
    c.background("installing.png", darken=0.22)
    c.radial_glow(480, 330, 400, 200, (0, 0, 0), 0.55, 50)

    c.logo(480, 108, 190)
    brand(c, 480, 196, 36)
    c.text(480, 250, "Instalando o KAIRON WA...", "inter-bold", 28, align="center")
    c.text(480, 296, "Aguarde enquanto os arquivos são copiados para o seu computador.", "inter", 16,
           fill=MUTED, align="center")

    # Barra de progresso
    x1, y1, x2, y2 = PROGRESS_BOX
    hh = (y2 - y1) / 2
    c.rrect(PROGRESS_BOX, hh, fill=(4, 16, 11, 235))
    if bar_full:
        c.rrect((x1, y1, x2, y2), hh, fill=GREEN + (150,), blur=6)
        c.rrect_gradient(PROGRESS_BOX, hh, (120, 255, 190), (24, 222, 122))
        c.hline_fade(x1 + 8, x2 - 8, y1 + 3, (255, 255, 255), 0.5)
    c.rrect(PROGRESS_BOX, hh, outline=(90, 255, 170, 80), width=1)

    # Cartão das etapas
    c.rrect(STAGE_CARD, 14, fill=(3, 14, 9, 200))
    c.rrect(STAGE_CARD, 14, outline=GREEN + (90,), width=4, blur=4)
    c.rrect(STAGE_CARD, 14, outline=(110, 255, 185, 170), width=1.3)
    stages = [(icon_file, "Copiando", "arquivos"), (icon_gear, "Configurando", "dependências"),
              (icon_database, "Registrando", "componentes"), (icon_shield, "Finalizando", "a instalação")]
    for i, (ico, l1, l2) in enumerate(stages):
        cx1, cx2 = STAGE_COLS[i]
        if i:
            c.line([(cx1, STAGE_CARD[1] + 18), (cx1, STAGE_CARD[3] - 18)], (120, 255, 190, 45), 1)
        ico(c, cx1 + 26, 412, 32)
        c.text(cx1 + 72, 410, l1, "inter-medium", 14.5)
        c.text(cx1 + 72, 431, l2, "inter", 14.5, fill=MUTED)
        _stage_marker(c, stage_mark_cx(i), STAGE_MARK_Y, mark_state)

    # Assinatura DMFV
    c.text(40, 562, "DMFV", "brand", 30, weight=800, tracking=1, gradient=METAL)
    c.text(42, 597, "AUDIO DESIGN", "inter-medium", 10.5, fill=(210, 220, 215), tracking=2.6, shadow=False)
    wave = []
    for i in range(0, 101):
        t = i / 100
        amp = math.exp(-((t - 0.45) ** 2) / 0.03) * 13 + 1.2
        wave.append((150 + t * 110, 582 + math.sin(t * 46) * amp * (0.6 + 0.4 * math.sin(t * 13))))
    c.line(wave, GREEN + (140,), 3, blur=2)
    c.line(wave, (120, 255, 190, 255), 1.3)

    button_secondary(c, INSTALL_CANCEL, "Cancelar")
    return c.final()


def render_finished(p):
    c = Canvas(p)
    c.background("finished.png", darken=0.22)
    c.radial_glow(480, 360, 380, 170, (0, 0, 0), 0.55, 50)

    c.logo(480, 122, 200)
    # Anel de sucesso
    cx, cy, r = 480, 268, 27
    c.ellipse((cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4), outline=GREEN + (160,), width=6, blur=5)
    c.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(3, 20, 12, 200), outline=GREEN_LIGHT + (255,), width=2.6)
    c.line([(cx - 11, cy + 1), (cx - 3, cy + 9), (cx + 12, cy - 8)], (235, 255, 245, 255), 3.6)

    c.text(480, 312, "Instalação concluída com sucesso!", "inter-bold", 31, align="center")
    c.text(480, 364, "O KAIRON WA foi instalado e está pronto para ser usado", "inter", 17, fill=MUTED,
           align="center")
    c.text(480, 389, "no seu computador.", "inter", 17, fill=MUTED, align="center")

    # Botão Concluir (vidro verde)
    x1, y1, x2, y2 = FINISH_BUTTON
    c.rrect((x1 - 3, y1 - 3, x2 + 3, y2 + 3), 14, fill=GREEN + (110,), blur=12)
    c.rrect_gradient(FINISH_BUTTON, 12, (22, 92, 56), (6, 34, 20), alpha=235)
    c.rrect(FINISH_BUTTON, 12, outline=(130, 255, 195, 255), width=2)
    c.hline_fade(x1 + 14, x2 - 14, y1 + 3, (255, 255, 255), 0.45)
    tw = c.text_width("Concluir", "inter-semibold", 22)
    tx = (x1 + x2) / 2 - (tw + 40) / 2
    c.text(tx, y1 + 15, "Concluir", "inter-semibold", 22)
    ax = tx + tw + 18
    ay = y1 + 30
    c.line([(ax, ay), (ax + 20, ay)], (255, 255, 255, 255), 2.4)
    c.line([(ax + 12, ay - 7), (ax + 20, ay), (ax + 12, ay + 7)], (255, 255, 255, 255), 2.4)
    c.hline_fade(x1 + 30, x2 - 30, y2 + 14, GREEN, 0.25)
    return c.final()


# ---------------------------------------------------------------- saída
def save_bmp(img: Image.Image, name: str):
    img.convert("RGB").save(os.path.join(OUT, name), "BMP")


def crop(img, box, p):
    x1, y1, x2, y2 = box
    return img.crop((S(x1, p), S(y1, p), S(x2, p), S(y2, p)))


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".bmp"):
            os.remove(os.path.join(OUT, f))
    for p in SCALES:
        save_bmp(render_welcome(p), f"welcome_{p}.bmp")
        base = render_installing(p)
        save_bmp(base, f"installing_{p}.bmp")
        full = render_installing(p, bar_full=True)
        save_bmp(crop(full, PROGRESS_BOX, p), f"progress_{p}.bmp")
        for state in ("active", "done"):
            img = render_installing(p, mark_state=state)
            for i in range(4):
                cx = stage_mark_cx(i)
                b = (cx - STAGE_MARK_BOX, STAGE_MARK_Y - STAGE_MARK_BOX,
                     cx + STAGE_MARK_BOX, STAGE_MARK_Y + STAGE_MARK_BOX)
                save_bmp(crop(img, b, p), f"stage{i + 1}_{state}_{p}.bmp")
            # o estado "pendente" é o próprio fundo; também salvamos para poder voltar
        for i in range(4):
            cx = stage_mark_cx(i)
            b = (cx - STAGE_MARK_BOX, STAGE_MARK_Y - STAGE_MARK_BOX,
                 cx + STAGE_MARK_BOX, STAGE_MARK_Y + STAGE_MARK_BOX)
            save_bmp(crop(base, b, p), f"stage{i + 1}_pending_{p}.bmp")
        save_bmp(render_finished(p), f"finished_{p}.bmp")
        print(f"escala {p}% ok")


if __name__ == "__main__":
    main()
