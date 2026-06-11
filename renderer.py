"""
renderer.py — Desenho das peças, dado, painel lateral e telas de fim/menu.
"""
import pygame
import math
from constants import (
    W, H, SIDE_W, CELL, BX, BY,
    WHITE, BLACK, LGRAY, DGRAY, BG,
    PC, PL, PN, YARDS, gpx
)

# ── Fontes ────────────────────────────────────────────────────────────────────
pygame.font.init()
F_BIG = pygame.font.SysFont("Arial", 36, bold=True)
F_MED = pygame.font.SysFont("Arial", 22, bold=True)
F_SM  = pygame.font.SysFont("Arial", 16)
F_XSM = pygame.font.SysFont("Arial", 13)


def _txt(surf, text, font, color, cx, cy, anchor="c"):
    img = font.render(str(text), True, color)
    r   = img.get_rect()
    if anchor == "c":  r.center  = (cx, cy)
    if anchor == "tl": r.topleft = (cx, cy)
    if anchor == "tc": r.midtop  = (cx, cy)
    surf.blit(img, r)


# ── Dado ──────────────────────────────────────────────────────────────────────
_DIE_DOTS = {
    1: [(0, 0)],
    2: [(-1, -1), (1,  1)],
    3: [(-1, -1), (0,  0), (1, 1)],
    4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
    5: [(-1, -1), (1, -1), (0,  0), (-1, 1), (1, 1)],
    6: [(-1, -1), (1, -1), (-1, 0), (1,  0), (-1, 1), (1, 1)],
}


def draw_die(surf, val, spinning, cx, cy, size=60):
    shadow = pygame.Rect(cx - size//2 + 3, cy - size//2 + 3, size, size)
    rect   = pygame.Rect(cx - size//2,     cy - size//2,     size, size)
    pygame.draw.rect(surf, (15, 15, 25), shadow, border_radius=10)
    pygame.draw.rect(surf, (245, 245, 245), rect, border_radius=10)
    pygame.draw.rect(surf, DGRAY, rect, 2,          border_radius=10)
    dot_col = (180, 40, 40) if spinning else (25, 25, 25)
    for dx, dy in _DIE_DOTS.get(val, []):
        pygame.draw.circle(surf, dot_col, (cx + dx*16, cy + dy*16), 7)


# ── Peças ─────────────────────────────────────────────────────────────────────
_OFFSETS4 = [(-7, -7), (7, -7), (-7, 7), (7, 7)]


def draw_pieces(surf, game):
    # Contar peças por célula para deslocamento
    cell_cnt = {}
    for pl in game.players:
        for p in pl.pieces:
            if p.state == "active":
                g = p.grid
                if g:
                    cell_cnt[g] = cell_cnt.get(g, 0) + 1
    cell_ord = {}

    anim_p  = game.anim_piece
    astep   = (min(game.anim_step, len(game.anim_path) - 1)
               if game.anim_path else 0)

    for pl in game.players:
        for p in pl.pieces:
            if p.state == "done":
                continue

            # Posição pixel
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

            highlighted = (p in game.movable and game.phase == "pick")
            _draw_single_piece(surf, p.pid, p.idx, px, py, highlighted)


def _draw_single_piece(surf, pid, idx, px, py, highlighted):
    r = CELL // 2 - 4
    if highlighted:
        pygame.draw.circle(surf, (255, 255,  60), (px, py), r + 6)
        pygame.draw.circle(surf, (200, 180,   0), (px, py), r + 6, 2)
    # Sombra
    pygame.draw.circle(surf, (0, 0, 0, 80), (px + 2, py + 2), r)
    # Corpo
    pygame.draw.circle(surf, PC[pid], (px, py), r)
    # Anel interno branco
    pygame.draw.circle(surf, WHITE, (px, py), r - 2, 2)
    # Número
    lbl = F_XSM.render(str(idx + 1), True, WHITE)
    surf.blit(lbl, (px - lbl.get_width()//2, py - lbl.get_height()//2))


# ── Painel lateral ────────────────────────────────────────────────────────────
def draw_sidebar(surf, game):
    sx = 6   # margem esquerda dentro do painel

    # Título
    _txt(surf, "LUDO", F_BIG, WHITE, SIDE_W//2, 30)

    # Cards dos jogadores
    for i, pl in enumerate(game.players):
        y   = 68 + i * 84
        act = (i == game.turn and game.phase != "end")
        bg  = PC[pl.pid] if act else (48, 48, 68)
        pygame.draw.rect(surf, bg, (sx, y, SIDE_W - sx*2, 76), border_radius=9)
        if act:
            pygame.draw.rect(surf, (255, 255, 100),
                             (sx, y, SIDE_W - sx*2, 76), 2, border_radius=9)

        _txt(surf, PN[pl.pid],              F_SM,  WHITE, SIDE_W//2, y + 16)
        _txt(surf, "Humano" if pl.human else "CPU",
             F_XSM, (230, 230, 230) if act else (150, 150, 150),
             SIDE_W//2, y + 33)

        # Pips de progresso
        fin = sum(1 for p in pl.pieces if p.state == "done")
        for k in range(4):
            c = WHITE if k < fin else PL[pl.pid]
            cx_ = sx + 12 + k * 30
            pygame.draw.circle(surf, c, (cx_, y + 58), 9)
            pygame.draw.circle(surf, PC[pl.pid] if k < fin else (60,60,80),
                               (cx_, y + 58), 9, 2)

    # Placar
    if game.rankings:
        ry = 72 + len(game.players) * 84 + 8
        _txt(surf, "Placar", F_XSM, (160, 160, 180), SIDE_W//2, ry)
        medals = ["🥇", "🥈", "🥉", "4º"]
        mcols  = [(255,215,0),(200,200,200),(180,130,50),(180,180,180)]
        for ri, pid in enumerate(game.rankings):
            _txt(surf, f"{medals[min(ri,3)]} {PN[pid]}",
                 F_XSM, mcols[min(ri,3)], SIDE_W//2, ry + 18 + ri * 20)

    # Dado
    dcx, dcy = SIDE_W//2, H - 165
    spinning = game.dice_spin > 0
    val = game.dice_show if spinning else (game.roll if game.roll else game.dice_final)
    draw_die(surf, val, spinning, dcx, dcy)

    # Dica de controle
    cp = game.cp()
    if game.phase == "roll" and cp.human and not spinning:
        _txt(surf, "ESPAÇO = rolar", F_XSM, (200, 200, 80), SIDE_W//2, H - 95)
    elif game.phase == "pick":
        _txt(surf, "Clique na peça", F_XSM, (200, 200, 80), SIDE_W//2, H - 95)
    elif not cp.human and game.phase in ("roll", "aipick", "anim"):
        _txt(surf, "CPU pensando...", F_XSM, (160, 160, 180), SIDE_W//2, H - 95)

    # Mensagem
    if game.msg:
        _wrap_text(surf, game.msg, F_XSM, (255, 220, 80), SIDE_W//2, H - 72, 20)


def _wrap_text(surf, text, font, color, cx, y_start, max_chars):
    words = text.split()
    line, lines = "", []
    for w in words:
        test = (line + " " + w).strip()
        if len(test) <= max_chars:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    for li, l in enumerate(lines[-4:]):
        _txt(surf, l, font, color, cx, y_start + li * 16)


# ── Tela de fim ───────────────────────────────────────────────────────────────
def draw_end_screen(surf, game):
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 175))
    surf.blit(ov, (0, 0))

    _txt(surf, "🏆  FIM DE JOGO!", F_BIG, (255, 220, 30), W//2, H//2 - 130)

    medals = ["🥇  1º lugar", "🥈  2º lugar", "🥉  3º lugar", "4º lugar"]
    mcols  = [(255,215,0),(210,210,210),(180,130,50),(180,180,180)]
    for ri, pid in enumerate(game.rankings):
        col = mcols[min(ri, 3)]
        _txt(surf, f"{medals[min(ri,3)]}: {PN[pid]}",
             F_MED, col, W//2, H//2 - 60 + ri * 48)

    pygame.draw.rect(surf, (45, 150, 45),
                     (W//2 - 95, H//2 + 148, 190, 48), border_radius=12)
    _txt(surf, "[R]  Reiniciar", F_MED, WHITE, W//2, H//2 + 172)
