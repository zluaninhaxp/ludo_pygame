"""
constants.py — Layout, paleta e caminhos do Ludo.
Suporta redimensionamento dinâmico via resize(w, h).
"""

import pygame

FPS = 60

# ── Paleta (estática) ─────────────────────────────────────────────────────────
WHITE  = (255, 255, 255)
BLACK  = (30,  28,  40)
CREAM  = (255, 250, 235)
LGRAY  = (215, 210, 225)
DGRAY  = (100,  90, 120)
BG     = (42,  34,  74)

PC = {
    0: (235,  70,  90),
    1: ( 50, 195, 120),
    2: ( 70, 140, 230),
    3: (250, 185,  30),
}
PL = {
    0: (255, 185, 195),
    1: (165, 240, 195),
    2: (175, 210, 255),
    3: (255, 230, 140),
}
PD = {
    0: (170,  30,  50),
    1: ( 20, 140,  80),
    2: ( 35,  85, 175),
    3: (190, 135,  10),
}
PN = {0:"Vermelho", 1:"Verde", 2:"Azul", 3:"Amarelo"}

# ── Elenco de personagens disponíveis ────────────────────────────────────────
CHARACTER_ROSTER = [
    ("caruzo",   "Caruzo"),
    ("miguel",   "Miguel"),
    ("darosa",   "Da Rosa"),
    ("joaop",    "João Pedro"),
]

CHARACTER_NAMES = {slug: name for slug, name in CHARACTER_ROSTER}

PLAYER_CHOICES = {
    0: "caruzo",
    1: "miguel",
    2: "darosa",
    3: "joaop"
}

PLAYER_DISPLAY_NAMES = {
    0: "Caruzo",
    1: "Miguel",
    2: "Da Rosa",
    3: "João P.",
}

# ── Caminho principal 52 casas (grade lógica) ─────────────────────
MPATH = (
      [(c,6) for c in range(1,6)]
    + [(6,r) for r in range(5,-1,-1)]
    + [(7,0),(8,0)]
    + [(8,r) for r in range(1,6)]
    + [(c,6) for c in range(9,14)]
    + [(14,6),(14,7),(14,8)]
    + [(c,8) for c in range(13,8,-1)]
    + [(8,r) for r in range(9,14)]
    + [(8,14),(7,14),(6,14)]
    + [(6,r) for r in range(13,8,-1)]
    + [(c,8) for c in range(5,0,-1)]
    + [(0,8),(0,7),(0,6)]
)
assert len(MPATH) == 52

ENTRY = {0:0, 1:13, 2:26, 3:39}

HSTRETCH = {
    0: [(c,7) for c in range(1,6)],
    1: [(7,r) for r in range(1,6)],
    2: [(c,7) for c in range(13,8,-1)],
    3: [(7,r) for r in range(13,8,-1)],
}

CENTER = (7,7)

SAFE = {
    MPATH[0], MPATH[8], MPATH[13], MPATH[21],
    MPATH[26], MPATH[34], MPATH[39], MPATH[47],
}

# ── Variáveis de layout (recalculadas por resize) ────────────────────────────
W      = 960
H      = 720
SIDE_W = 160
BSIZE  = 660
BX     = 170
BY     = 30
CELL   = 44

BASE_SCALE  = 0.82
BASE_SZ     = int(CELL * 6 * BASE_SCALE)
BASE_OFFSET = (CELL * 6 - BASE_SZ) // 2
B_CELL      = BASE_SZ / 6.0

YARDS: dict = {}

def _recalc_yards():
    YARDS.clear()
    YARDS.update({
        0: _yard(0, 0),
        1: _yard(9, 0),
        2: _yard(9, 9),
        3: _yard(0, 9),
    })

def _yard(oc, or_):
    sz     = CELL * 5.9
    sobra  = CELL * 6 - sz
    offset_x = sobra if oc == 9 else 0
    offset_y = sobra if or_ == 9 else 0
    px = BX + oc * CELL + offset_x
    py = BY + or_ * CELL + offset_y
    cx_base = px + sz / 2
    cy_base = py + sz / 2
    spread  = 1.05
    pts = []
    for dr in [-1, 1]:
        for dc in [-1, 1]:
            cx_ = cx_base + dc * spread * CELL
            cy_ = cy_base + dr * spread * CELL
            pts.append((int(cx_), int(cy_)))
    return pts

def gpx(col, row):
    return (BX + col * CELL + CELL // 2, BY + row * CELL + CELL // 2)

def steps_to_px(pid, steps):
    # Correção da conversão de esquina
    if steps <= 50:
        return gpx(*MPATH[(ENTRY[pid] + steps) % 52])
    hs = steps - 51
    if hs < 5:
        return gpx(*HSTRETCH[pid][hs])
    return gpx(*CENTER)

# ── Função principal de redimensionamento ─────────────────────────────────────
def resize(new_w: int, new_h: int):
    global W, H, SIDE_W, BSIZE, BX, BY, CELL
    global BASE_SCALE, BASE_SZ, BASE_OFFSET, B_CELL

    W = new_w
    H = new_h

    SIDE_W = max(120, min(200, int(new_w * 0.167)))
    area_w = new_w - SIDE_W
    area_h = new_h
    margin = max(16, int(min(area_w, area_h) * 0.03))
    BSIZE  = (min(area_w, area_h) - margin * 2) // 15 * 15  

    CELL   = BSIZE // 15
    BX = SIDE_W + (area_w - BSIZE) // 2
    BY = (area_h - BSIZE) // 2

    BASE_SCALE  = 0.82
    BASE_SZ     = int(CELL * 6 * BASE_SCALE)
    BASE_OFFSET = (CELL * 6 - BASE_SZ) // 2
    B_CELL      = BASE_SZ / 6.0

    _recalc_yards()

_recalc_yards()