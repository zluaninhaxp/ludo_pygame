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

# ── Janela ─────────────────────────────────────────────────────────────────────
W, H    = 960, 720
SIDE_W  = 160
BSIZE   = 600
BX      = SIDE_W
BY      = (H - BSIZE) // 2   # 60
CELL    = BSIZE // 15         # 40
FPS     = 60

# ── Paleta ─────────────────────────────────────────────────────────────────────
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
CREAM  = (250, 248, 240)
LGRAY  = (200, 200, 200)
DGRAY  = (80,  80,  80)
BG     = (24,  24,  40)

PC = {0:(204,40,40), 1:(34,160,34), 2:(40,100,210), 3:(210,165,20)}
PL = {0:(255,180,180), 1:(160,235,160), 2:(160,195,255), 3:(255,230,120)}
PN = {0:"Vermelho", 1:"Verde", 2:"Azul", 3:"Amarelo"}

# ── Caminho principal 52 casas ─────────────────────────────────────────────────
MPATH = (
      [(c,6) for c in range(1,6)]          # 0-4   Red entry row-6 →
    + [(6,r) for r in range(5,-1,-1)]      # 5-10  col-6 ↑
    + [(7,0),(8,0)]                        # 11-12 top corridor →
    + [(8,r) for r in range(1,6)]          # 13-17 Green entry col-8 ↓
    + [(c,6) for c in range(9,14)]         # 18-22 row-6 →
    + [(14,6),(14,7),(14,8)]               # 23-25 right corridor ↓
    + [(c,8) for c in range(13,8,-1)]      # 26-30 Blue entry row-8 ←
    + [(8,r) for r in range(9,14)]         # 31-35 col-8 ↓
    + [(8,14),(7,14),(6,14)]               # 36-38 bottom corridor ←
    + [(6,r) for r in range(13,8,-1)]      # 39-43 Yellow entry col-6 ↑
    + [(c,8) for c in range(5,0,-1)]       # 44-48 row-8 ←
    + [(0,8),(0,7),(0,6)]                  # 49-51 left corridor ↑
)
assert len(MPATH) == 52
assert MPATH[0]  == (1,6)
assert MPATH[13] == (8,1)
assert MPATH[26] == (13,8)
assert MPATH[39] == (6,13)

ENTRY = {0:0, 1:13, 2:26, 3:39}

HSTRETCH = {
    0: [(c,7) for c in range(1,6)],          # Vermelho row-7 →
    1: [(7,r) for r in range(1,6)],          # Verde    col-7 ↓
    2: [(c,7) for c in range(13,8,-1)],      # Azul     row-7 ←
    3: [(7,r) for r in range(13,8,-1)],      # Amarelo  col-7 ↑
}

CENTER = (7,7)

SAFE = {
    MPATH[0], MPATH[8], MPATH[13], MPATH[21],
    MPATH[26], MPATH[34], MPATH[39], MPATH[47],
}

def _yard(bc, br):
    return [(BX+(bc+dc)*CELL+CELL//2, BY+(br+dr)*CELL+CELL//2)
            for dr in range(2) for dc in range(2)]

YARDS = {0:_yard(1,1), 1:_yard(10,1), 2:_yard(10,10), 3:_yard(1,10)}

def gpx(col, row):
    return (BX + col*CELL + CELL//2, BY + row*CELL + CELL//2)

def steps_to_px(pid, steps):
    if steps <= 51:
        return gpx(*MPATH[(ENTRY[pid]+steps)%52])
    hs = steps - 52
    if hs < 5:
        return gpx(*HSTRETCH[pid][hs])
    return gpx(*CENTER)
