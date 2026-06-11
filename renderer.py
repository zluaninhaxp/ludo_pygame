"""
renderer.py — Peças, dado, sidebar e telas de fim.
Estilo: cute / flat-vector / sticker.

Linguagem visual (consistente com board.py):
  · Cores planas e saturadas — zero alpha, zero gradiente
  · Sombras flat sólidas (offset 3 px, cor escura sólida)
  · Contorno universal _INK (roxo-escuro) espessura 2
  · Flat highlight: faixa/retângulo sólido branco no topo dos elementos
  · Peças: 3 camadas (sombra → corpo → anel claro) + highlight retangular
  · Dado: corpo flat + highlight retangular branco no topo
  · Sidebar: cards limpos com mesmo vocabulário visual
"""
import pygame
import math
import os 
from constants import (
    W, H, SIDE_W, CELL, BX, BY,
    WHITE, BLACK, BG,
    PC, PL, PD, PN, YARDS, gpx,
)

# ── Fontes ────────────────────────────────────────────────────────────────────
pygame.font.init()

def _load_font(size, bold=False):
    for name in ("Fredoka One", "Nunito", "Varela Round",
                 "Comic Sans MS", "Arial Rounded MT Bold"):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.SysFont("Arial", size, bold=bold)

F_BIG = _load_font(36, bold=True)
F_MED = _load_font(22, bold=True)
F_SM  = _load_font(16, bold=True)
F_XSM = _load_font(13)

# ── Paleta UI ────────────────────────────────────────────────────────────────
_INK         = (52,  42,  76)
_PANEL_BG    = (36,  26,  64)
_PANEL_EDGE  = (72,  58, 112)
_CARD_IDLE   = (54,  42,  86)
_CARD_SH     = (20,  14,  42)
_HINT_COL    = (255, 222,  60)
_HINT_BG     = (62,  50,  98)
_DIM         = (125, 112, 158)
_RANK_GOLD   = (255, 208,   0)
_RANK_SILVER = (198, 198, 198)
_RANK_BRONZE = (190, 130,  50)

_SH_OFF = 3


def _sh(color, amt=45):
    return (max(color[0]-amt, 0), max(color[1]-amt, 0), max(color[2]-amt, 0))


# ── Texto ─────────────────────────────────────────────────────────────────────
def _txt(surf, text, font, color, cx, cy, anchor="c"):
    img = font.render(str(text), True, color)
    r   = img.get_rect()
    if   anchor == "c":  r.center  = (cx, cy)
    elif anchor == "tl": r.topleft = (cx, cy)
    elif anchor == "tc": r.midtop  = (cx, cy)
    surf.blit(img, r)


def _txt_sh(surf, text, font, color, cx, cy, sh_col=None, off=2):
    sc = sh_col or _sh(color, 90)
    _txt(surf, text, font, sc,    cx + off, cy + off)
    _txt(surf, text, font, color, cx,       cy)


# ── Dado ──────────────────────────────────────────────────────────────────────
_DIE_DOTS = {
    1: [(0, 0)],
    2: [(-1, -1), ( 1,  1)],
    3: [(-1, -1), ( 0,  0), (1,  1)],
    4: [(-1, -1), ( 1, -1), (-1, 1), (1, 1)],
    5: [(-1, -1), ( 1, -1), ( 0,  0), (-1, 1), (1, 1)],
    6: [(-1, -1), ( 1, -1), (-1,  0), ( 1, 0), (-1, 1), (1, 1)],
}


def draw_die(surf, val, spinning, cx, cy, size=56):
    rad = 11
    face  = (255, 250, 238) if not spinning else (255, 234, 176)
    border= (92,  74, 152) if not spinning else (235, 162,  28)
    rect  = pygame.Rect(cx - size//2, cy - size//2, size, size)

    # Corpo
    pygame.draw.rect(surf, face, rect, border_radius=rad)
    # Borda colorida
    pygame.draw.rect(surf, border, rect, 3, border_radius=rad)
    # Contorno ink (sticker)
    pygame.draw.rect(surf, _INK, rect, 1, border_radius=rad)

    # Pontos do dado
    dot_fill = (212, 42, 68) if spinning else (46,  36, 72)
    dot_sh   = _sh(dot_fill, 55)
    step     = 14
    r_dot    = 5
    for dx, dy in _DIE_DOTS.get(val, []):
        px_ = cx + dx * step
        py_ = cy + dy * step
        pygame.draw.circle(surf, dot_sh,  (px_ + 1, py_ + 1), r_dot)
        pygame.draw.circle(surf, dot_fill,(px_,     py_),      r_dot)


# ── Gerenciador de Imagens (Rostos) ───────────────────────────────────────────
_PIECE_IMAGES = {}

def _get_piece_image(pid, radius):
    """Carrega a foto, redimensiona mantendo a proporção (sem amassar) e centraliza."""
    key = (pid, radius)
    if key in _PIECE_IMAGES:
        return _PIECE_IMAGES[key]

    size = radius * 2
    path = os.path.join("images", f"player_{pid}.png")
    
    # Cria a superfície final com fundo transparente
    final_img = pygame.Surface((size, size), pygame.SRCALPHA)
    
    try:
        img = pygame.image.load(path).convert_alpha()
        orig_w, orig_h = img.get_size()

        # MÁGICA DA PROPORÇÃO: Pega o menor fator de escala para garantir que caiba perfeitamente
        scale = min(size / orig_w, size / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        # Redimensiona a imagem usando o mesmo fator para largura e altura (não distorce!)
        img = pygame.transform.smoothscale(img, (new_w, new_h))

        # Calcula a posição X e Y para centralizar a imagem na superfície
        pos_x = (size - new_w) // 2
        pos_y = (size - new_h) // 2
        
        # Como são PNGs transparentes, colamos direto no centro sem usar máscara
        final_img.blit(img, (pos_x, pos_y))

    except Exception:
        # Fallback caso a imagem não seja encontrada na pasta
        pygame.draw.circle(final_img, PL[pid], (radius, radius), radius)

    _PIECE_IMAGES[key] = final_img
    return final_img


def draw_pieces(surf, game):
    cell_cnt = {}
    for pl in game.players:
        for p in pl.pieces:
            if p.state == "active" and p.grid:
                cell_cnt[p.grid] = cell_cnt.get(p.grid, 0) + 1
    cell_ord = {}

    anim_p = game.anim_piece
    astep  = (min(game.anim_step, len(game.anim_path) - 1)
              if game.anim_path else 0)

    for pl in game.players:
        for p in pl.pieces:
            if p.state == "done":
                continue
            if p is anim_p and game.anim_path:
                px, py = game.anim_path[astep]
            elif p.state == "home":
                px, py = YARDS[p.pid][p.idx]
            elif p.state == "active":
                g = p.grid
                if g is None:
                    continue
                ox, oy = 0, 0
                if cell_cnt.get(g, 1) > 1:
                    k = cell_ord.get(g, 0)
                    cell_ord[g] = k + 1
                    ox, oy = _OFFSETS4[k % 4]
                bx, by = gpx(*g)
                px, py = bx + ox, by + oy
            else:
                continue

            sel = (p in game.movable and game.phase == "pick")
            _draw_piece(surf, p.pid, p.idx, px, py, sel)


def _draw_piece(surf, pid, idx, px, py, sel):
    """
    Token com foto do jogador (agora sem bordas duras, apenas o PNG):
      1. Anel de seleção (se selecionável)
      2. Sombra flutuante suave
      3. Imagem do rosto (proporcional)
      4. Badge (bottonzinho) com o número da peça
    """
    r = CELL // 2 - 5

    # 1 · Anel de seleção (quando é a vez de escolher quem anda)
    if sel:
        pygame.draw.circle(surf, _HINT_COL, (px, py), r + 6)
        pygame.draw.circle(surf, WHITE,     (px, py), r + 6, 2)

    # 2 · Sombra de elevação (mantemos uma sombrinha para o rosto não parecer liso no tabuleiro)
    pygame.draw.circle(surf, (0, 0, 0, 25), (px, py + 3), r - 1)

    # 3 · Imagem do rosto (proporcional e sem distorcer)
    img = _get_piece_image(pid, r)
    img_rect = img.get_rect(center=(px, py))
    surf.blit(img, img_rect)

    # 4 · Badge (Pequeno círculo no canto inferior direito com o número da peça)
    badge_r = 7
    bx, by = px + r - 5, py + r - 5
    
    # Fundo e contorno do badge (ajuda a identificar a cor do jogador)
    pygame.draw.circle(surf, PC[pid], (bx, by), badge_r)
    pygame.draw.circle(surf, WHITE,   (bx, by), badge_r, 2)
    
    # Número
    lbl = F_XSM.render(str(idx + 1), True, WHITE)
    surf.blit(lbl, (bx - lbl.get_width()  // 2,
                    by - lbl.get_height() // 2 + 1))


# ── Sidebar ───────────────────────────────────────────────────────────────────
def draw_sidebar(surf, game):
    sx   = 6
    cw   = SIDE_W - sx * 2
    ch   = 76

    # Fundo e borda do painel
    pygame.draw.rect(surf, _PANEL_BG,   (0, 0, SIDE_W, H))
    pygame.draw.rect(surf, _PANEL_EDGE, (0, 0, SIDE_W, H), 3)

    # Título
    _txt_sh(surf, "LUDO", F_BIG, _HINT_COL, SIDE_W // 2, 32)

    # Cards dos jogadores
    for i, pl in enumerate(game.players):
        y   = 66 + i * 84
        act = (i == game.turn and game.phase != "end")
        bg  = PC[pl.pid] if act else _CARD_IDLE

        # Corpo do card
        pygame.draw.rect(surf, bg,
                         (sx, y, cw, ch), border_radius=11)

            # Borda destaque
        pygame.draw.rect(surf, _HINT_COL,
                        (sx, y, cw, ch), 3, border_radius=11)

        # Contorno ink universal
        pygame.draw.rect(surf, _INK,
                         (sx, y, cw, ch), 1, border_radius=11)

        _txt(surf, PN[pl.pid], F_SM,  WHITE, SIDE_W // 2, y + 17)
        _txt(surf,
             "Humano" if pl.human else "CPU",
             F_XSM,
             (235, 228, 255) if act else _DIM,
             SIDE_W // 2, y + 35)

        # Pips de progresso — flat, sem oval gelatinoso
        fin = sum(1 for p in pl.pieces if p.state == "done")
        for k in range(4):
            cx_   = sx + 14 + k * 29
            cy_   = y + 60
            rp    = 8
            sh_c  = PD[pl.pid] if k < fin else (18, 12, 38)
            body  = WHITE      if k < fin else PL[pl.pid]
            edge  = PC[pl.pid] if k < fin else (60, 48, 92)

            pygame.draw.circle(surf, sh_c, (cx_ + 1, cy_ + 2), rp)
            pygame.draw.circle(surf, body, (cx_, cy_), rp)
            pygame.draw.circle(surf, edge, (cx_, cy_), rp, 2)
            if k < fin:
                pygame.draw.circle(surf, _INK, (cx_, cy_), rp, 1)

    # Placar (se houver)
    if game.rankings:
        ry    = 70 + len(game.players) * 84 + 10
        mcols = [_RANK_GOLD, _RANK_SILVER, _RANK_BRONZE, (148, 148, 148)]
        lbls  = ["#1", "#2", "#3", "#4"]
        _txt(surf, "Placar", F_XSM, _DIM, SIDE_W // 2, ry)
        for ri, pid in enumerate(game.rankings):
            _txt(surf, f"{lbls[min(ri,3)]} {PN[pid]}",
                 F_XSM, mcols[min(ri, 3)],
                 SIDE_W // 2, ry + 18 + ri * 20)

    # Dado
    dcx, dcy = SIDE_W // 2, H - 158
    spinning  = game.dice_spin > 0
    val = game.dice_show if spinning else (game.roll if game.roll else game.dice_final)
    draw_die(surf, val, spinning, dcx, dcy)

    # Balão de dica
    cp   = game.cp()
    hint = ""
    if game.phase == "roll" and cp.human and not spinning:
        hint = "ESPACO = rolar"
    elif game.phase == "pick":
        hint = "Clique na peca"
    elif not cp.human and game.phase in ("roll", "aipick", "anim"):
        hint = "CPU pensando..."

    if hint:
        hw = SIDE_W - 12
        hx = 6
        hy = H - 96
        # Corpo
        pygame.draw.rect(surf, _HINT_BG,
                         (hx, hy, hw, 28), border_radius=8)
        # Borda destaque + ink
        pygame.draw.rect(surf, _HINT_COL,
                         (hx, hy, hw, 28), 2, border_radius=8)
        pygame.draw.rect(surf, _INK,
                         (hx, hy, hw, 28), 1, border_radius=8)
        _txt(surf, hint, F_XSM, _HINT_COL, SIDE_W // 2, hy + 14)

    # Mensagem de jogo
    if game.msg:
        _wrap_text(surf, game.msg, F_XSM,
                   (255, 205, 85), SIDE_W // 2, H - 60, 20)


def _wrap_text(surf, text, font, color, cx, y0, max_chars):
    words = text.split()
    line, lines = "", []
    for w in words:
        t = (line + " " + w).strip()
        if len(t) <= max_chars:
            line = t
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    for li, l in enumerate(lines[-4:]):
        _txt(surf, l, font, color, cx, y0 + li * 16)


# ── Tela de fim ───────────────────────────────────────────────────────────────
def draw_end_screen(surf, game):
    # Overlay semi-opaco (SRCALPHA para escurecer sem sumir)
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((18, 10, 48, 205))
    surf.blit(ov, (0, 0))

    pw, ph = 430, 375
    px = W // 2 - pw // 2
    py = H // 2 - ph // 2 - 10

    # Painel principal
    pygame.draw.rect(surf, (46, 34, 84),
                     (px, py, pw, ph), border_radius=18)
    # Bordas
    pygame.draw.rect(surf, _HINT_COL,
                     (px, py, pw, ph), 4, border_radius=18)
    pygame.draw.rect(surf, _INK,
                     (px, py, pw, ph), 1, border_radius=18)

    _txt_sh(surf, "FIM DE JOGO!", F_BIG, _HINT_COL, W // 2, py + 46)

    # Plaquinhas de resultado
    mcols = [_RANK_GOLD, _RANK_SILVER, _RANK_BRONZE, (150, 150, 150)]
    lbls  = ["1o lugar", "2o lugar", "3o lugar", "4o lugar"]
    for ri, pid in enumerate(game.rankings):
        row_y = py + 102 + ri * 54
        plw, plh = 320, 40
        plx = W // 2 - plw // 2

        # Corpo
        pygame.draw.rect(surf, PC[pid],
                         (plx, row_y - plh//2, plw, plh), border_radius=10)
        # Bordas
        pygame.draw.rect(surf, PD[pid],
                         (plx, row_y - plh//2, plw, plh), 2, border_radius=10)
        pygame.draw.rect(surf, _INK,
                         (plx, row_y - plh//2, plw, plh), 1, border_radius=10)

        _txt_sh(surf, f"{lbls[min(ri,3)]}: {PN[pid]}",
                F_MED, WHITE, W // 2, row_y + 1)

    # Botão Reiniciar
    bx, by_ = W // 2 - 105, py + ph - 65
    bw, bh  = 210, 48

    pygame.draw.rect(surf, (10, 68, 10),
                     (bx + 3, by_ + 4, bw, bh), border_radius=12)
    pygame.draw.rect(surf, (50, 168, 50),
                     (bx, by_, bw, bh), border_radius=12)
    pygame.draw.rect(surf, (88, 208, 88),
                     (bx + 6, by_ + 5, bw - 12, bh // 4), border_radius=7)
    pygame.draw.rect(surf, (28, 118, 28),
                     (bx, by_, bw, bh), 2, border_radius=12)
    pygame.draw.rect(surf, _INK,
                     (bx, by_, bw, bh), 1, border_radius=12)

    _txt_sh(surf, "[R]  Reiniciar", F_MED, WHITE, W // 2, by_ + bh // 2 + 1)
