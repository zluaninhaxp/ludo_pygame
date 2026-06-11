"""
board.py — Desenho do tabuleiro.

Layout de cores (padrão oficial Ludo):
  - Zonas home 6x6 nos cantos: cor sólida do jogador, interior branco
  - Casas do caminho principal: CREAM (neutras) ou cor do jogador na entrada
  - Corredor de chegada (home stretch): cor clara do jogador
  - Centro 3x3: triângulos coloridos convergindo ao centro
  - Casas seguras: estrela dourada
  - Linhas de grade finas sobre tudo
"""
import pygame
import math
from constants import (
    BX, BY, BSIZE, CELL,
    WHITE, CREAM, LGRAY, DGRAY, BLACK,
    PC, PL, MPATH, HSTRETCH, CENTER, SAFE, ENTRY,
    gpx
)

# Casas do caminho que ficam na "faixa de entrada" de cada jogador
# (a primeira célula do path de cada um recebe a cor do jogador)
_ENTRY_CELLS = {MPATH[v]: k for k, v in ENTRY.items()}

# Conjunto completo de células do caminho para lookup rápido
_PATH_SET = set(MPATH)

# Células do corredor de chegada (todas) para lookup
_HSTRETCH_MAP = {}  # (col,row) -> pid
for _pid, _cells in HSTRETCH.items():
    for _cr in _cells:
        _HSTRETCH_MAP[_cr] = _pid


def _star(surf, color, cx, cy, r_outer=9, r_inner=4, points=6):
    pts = []
    for i in range(points * 2):
        a = math.pi / points * i - math.pi / 2
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pygame.draw.polygon(surf, color, pts)


def _cell_rect(col, row, margin=1):
    return pygame.Rect(
        BX + col * CELL + margin,
        BY + row * CELL + margin,
        CELL - margin * 2,
        CELL - margin * 2,
    )


def draw_board(surf: pygame.Surface):
    # ── 1. Fundo branco do tabuleiro ─────────────────────────────────────────
    pygame.draw.rect(surf, WHITE, (BX, BY, BSIZE, BSIZE))

    # ── 2. Zonas home (cantos 6×6) ───────────────────────────────────────────
    _home_origins = {0: (0, 0), 1: (9, 0), 2: (9, 9), 3: (0, 9)}
    for pid, (oc, or_) in _home_origins.items():
        px = BX + oc * CELL
        py = BY + or_ * CELL
        # Área sólida
        pygame.draw.rect(surf, PC[pid], (px, py, CELL * 6, CELL * 6))
        # Interior branco (4×4 centrado)
        pygame.draw.rect(surf, WHITE,
                         (px + CELL, py + CELL, CELL * 4, CELL * 4))
        # Círculos indicadores dos 4 spots do yard
        for dr in range(2):
            for dc in range(2):
                cx = px + CELL + dc * 2 * CELL + CELL
                cy = py + CELL + dr * 2 * CELL + CELL
                pygame.draw.circle(surf, PL[pid], (cx, cy), CELL * 3 // 4)
                pygame.draw.circle(surf, PC[pid], (cx, cy), CELL * 3 // 4, 3)

    # ── 3. Casas do caminho principal ────────────────────────────────────────
    for idx, (c, r) in enumerate(MPATH):
        rect = _cell_rect(c, r)
        # Células de entrada recebem a cor do respectivo jogador
        if (c, r) in _ENTRY_CELLS:
            pid = _ENTRY_CELLS[(c, r)]
            pygame.draw.rect(surf, PC[pid], rect)
        else:
            pygame.draw.rect(surf, CREAM, rect)

    # ── 4. Corredor de chegada (home stretch) ────────────────────────────────
    for (c, r), pid in _HSTRETCH_MAP.items():
        pygame.draw.rect(surf, PL[pid], _cell_rect(c, r))

    # ── 5. Centro 3×3 — triângulos coloridos ─────────────────────────────────
    ox = BX + 6 * CELL
    oy = BY + 6 * CELL
    cs = CELL * 3
    mid = (ox + cs // 2, oy + cs // 2)
    corners = [
        (ox,      oy),
        (ox + cs, oy),
        (ox + cs, oy + cs),
        (ox,      oy + cs),
    ]
    # Vermelho=topo-esq, Verde=topo-dir, Azul=baixo-dir, Amarelo=baixo-esq
    tri_pids = [0, 1, 2, 3]
    for i, pid in enumerate(tri_pids):
        pygame.draw.polygon(surf, PC[pid],
                            [corners[i], corners[(i + 1) % 4], mid])
    # Estrela central dourada
    _star(surf, (255, 220, 30), mid[0], mid[1], r_outer=14, r_inner=6, points=6)

    # ── 6. Estrelas nas casas seguras ────────────────────────────────────────
    for c, r in SAFE:
        # Não desenha estrela na entrada colorida (já é identificável)
        if (c, r) not in _ENTRY_CELLS:
            cx = BX + c * CELL + CELL // 2
            cy = BY + r * CELL + CELL // 2
            _star(surf, (255, 220, 30), cx, cy, r_outer=9, r_inner=4, points=6)

    # ── 7. Linhas de grade ───────────────────────────────────────────────────
    for i in range(16):
        x = BX + i * CELL
        y = BY + i * CELL
        pygame.draw.line(surf, LGRAY, (BX, y), (BX + BSIZE, y), 1)
        pygame.draw.line(surf, LGRAY, (x,  BY), (x, BY + BSIZE), 1)
    # Borda externa
    pygame.draw.rect(surf, DGRAY, (BX, BY, BSIZE, BSIZE), 2)
