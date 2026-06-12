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

# No seu constants.py
W, H    = 960, 720
SIDE_W  = 160
BSIZE   = 660  # Verifique se esta linha existe!

_AREA_LIVRE_W = W - SIDE_W
BX = SIDE_W + (_AREA_LIVRE_W - BSIZE) // 2   
BY = (H - BSIZE) // 2                        

CELL    = BSIZE // 15  # As casas agora têm 44 pixels!
FPS     = 60

# ── Escala da Base (O Truque da Ilusão) ───────────────────────────────────────
BASE_SCALE  = 0.82  # Encolhe as bases em 18%
BASE_SZ     = int(CELL * 6 * BASE_SCALE)
BASE_OFFSET = (CELL * 6 - BASE_SZ) // 2
B_CELL      = BASE_SZ / 6.0

# ── Paleta Cute/Vector ──────────────────────────────────────────────────────────
WHITE  = (255, 255, 255)
BLACK  = (30,  28,  40)
# Cream mais quente, lembrando papel de caderno
CREAM  = (255, 250, 235)
LGRAY  = (215, 210, 225)
DGRAY  = (100,  90, 120)
# Fundo principal: roxo-azul profundo bem saturado
BG     = (42,  34,  74)

# Paleta de jogadores: tons vibrantes mas suaves (não primários puros)
# Vermelho-cereja, Verde-menta, Azul-celeste, Amarelo-mel
PC = {
    0: (235,  70,  90),   # Vermelho cereja
    1: ( 50, 195, 120),   # Verde menta
    2: ( 70, 140, 230),   # Azul celeste
    3: (250, 185,  30),   # Amarelo mel
}
# Tons claros pastel de cada jogador (para home stretch, highlights)
PL = {
    0: (255, 185, 195),
    1: (165, 240, 195),
    2: (175, 210, 255),
    3: (255, 230, 140),
}
# Tons bem escuros de cada jogador (para sombras/contornos)
PD = {
    0: (170,  30,  50),
    1: ( 20, 140,  80),
    2: ( 35,  85, 175),
    3: (190, 135,  10),
}
PN = {0:"Vermelho", 1:"Verde", 2:"Azul", 3:"Amarelo"}

PLAYER_CHOICES = {
    0: "caruzo",    
    1: "miguel",   
    2: "darosa",  
    3: "joãop"      
}

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

def _yard(oc, or_):
    """Calcula os pixels dos buracos na base acompanhando as quinas."""
    sz = CELL * 5.9
    sobra = CELL * 6 - sz
    
    offset_x = sobra if oc == 9 else 0
    offset_y = sobra if or_ == 9 else 0
    
    px = BX + oc * CELL + offset_x
    py = BY + or_ * CELL + offset_y
    
    cx_base = px + sz / 2
    cy_base = py + sz / 2
    
    # IMPORTANTE: Tem que ser o mesmo valor usado no board.py!
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