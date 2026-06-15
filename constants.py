"""
constants.py — Layout, paleta e caminhos do Ludo.

Grade 15x15 (col c=0..14, row r=0..14):
  Vermelho  topo-esquerda   cols 0-5  / rows 0-5
  Verde     topo-direita    cols 9-14 / rows 0-5
  Azul      baixo-direita   cols 9-14 / rows 9-14
  Amarelo   baixo-esquerda  cols 0-5  / rows 9-14
  Corredor central cols 6-8, rows 6-8

Caminho principal 52 casas (sentido horário):
  idx  0  entrada Vermelho  (1,6)
  idx 13  entrada Verde     (8,1)
  idx 26  entrada Azul      (13,8)
  idx 39  entrada Amarelo   (6,13)
"""

W, H    = 960, 720
SIDE_W  = 160
BSIZE   = 660

_AREA_LIVRE_W = W - SIDE_W
BX = SIDE_W + (_AREA_LIVRE_W - BSIZE) // 2
BY = (H - BSIZE) // 2

CELL    = BSIZE // 15
FPS     = 60

# ── Escala da Base ─────────────────────────────────────────────────────────────
BASE_SCALE  = 0.82
BASE_SZ     = int(CELL * 6 * BASE_SCALE)
BASE_OFFSET = (CELL * 6 - BASE_SZ) // 2
B_CELL      = BASE_SZ / 6.0

# ── Paleta ─────────────────────────────────────────────────────────────────────
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

# ── Nomes dos slots (agora dinâmico — sobrescrito pelo menu) ───────────────────
# Estes são os defaults; o menu atualiza PN com o nome real do personagem.
PN = {0: "Jogador 1", 1: "Jogador 2", 2: "Jogador 3", 3: "Jogador 4"}

# ── Catálogo de personagens ────────────────────────────────────────────────────
# Chave: nome do arquivo (sem .png) em images/
# Valor: nome de exibição amigável
# Adicione/remova entradas conforme suas imagens.
CHARACTER_CATALOG = [
    {"key": "caruzo",   "name": "Caruzo"},
    {"key": "miguel",   "name": "Miguel"},
    {"key": "darosa",   "name": "Da Rosa"},
    {"key": "joaop",    "name": "João Pedro"},
]

# Escolhas ativas (pid → key do personagem). Atualizado pelo menu antes do jogo.
PLAYER_CHOICES = {
    0: CHARACTER_CATALOG[0]["key"],
    1: CHARACTER_CATALOG[1]["key"],
    2: CHARACTER_CATALOG[2]["key"],
    3: CHARACTER_CATALOG[3]["key"],
}

# ── Caminho principal 52 casas ─────────────────────────────────────────────────
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
assert MPATH[0]  == (1,6)
assert MPATH[13] == (8,1)
assert MPATH[26] == (13,8)
assert MPATH[39] == (6,13)

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

def _yard(oc, or_):
    sz = CELL * 5.9
    sobra = CELL * 6 - sz
    offset_x = sobra if oc == 9 else 0
    offset_y = sobra if or_ == 9 else 0
    px = BX + oc * CELL + offset_x
    py = BY + or_ * CELL + offset_y
    cx_base = px + sz / 2
    cy_base = py + sz / 2
    spread = 1.05
    pts = []
    for dr in [-1, 1]:
        for dc in [-1, 1]:
            cx_ = cx_base + dc * spread * CELL
            cy_ = cy_base + dr * spread * CELL
            pts.append((int(cx_), int(cy_)))
    return pts

YARDS = {
    0: _yard(0, 0),
    1: _yard(9, 0),
    2: _yard(9, 9),
    3: _yard(0, 9)
}

def gpx(col, row):
    return (BX + col*CELL + CELL//2, BY + row*CELL + CELL//2)

def steps_to_px(pid, steps):
    if steps <= 51:
        return gpx(*MPATH[(ENTRY[pid]+steps)%52])
    hs = steps - 52
    if hs < 5:
        return gpx(*HSTRETCH[pid][hs])
    return gpx(*CENTER)