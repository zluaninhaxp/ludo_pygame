"""
board.py — Tabuleiro estilo cute / flat-vector / sticker.

Linguagem visual:
  · Cores planas e saturadas — zero gradiente, zero alpha
  · Sombras flat sólidas (offset 3–4 px, cor escura sólida)
  · Contorno universal _INK (roxo-escuro, não preto puro)  espessura 2
  · Sem grid de linhas
  · Home stretch: todas as 5 casas com PC[pid] uniforme
  · Estrelas "gordas" de 5 pontas — robustas, highlight geométrico sólido
  · Casas do caminho NÃO invadem as zonas home (margin = CELL//10 + 1)
"""
import pygame
import math
from constants import (
    BX, BY, BSIZE, CELL,
    WHITE, CREAM,
    PC, PL, PD, MPATH, HSTRETCH, CENTER, SAFE, ENTRY,
    gpx, BASE_SZ, BASE_OFFSET, B_CELL  # <--- ADICIONE ESTAS TRÊS AQUI
)

# ── Mapas de lookup ──────────────────────────────────────────────────────────
_ENTRY_CELLS  = {MPATH[v]: k for k, v in ENTRY.items()}
_HSTRETCH_MAP = {}
for _pid, _cells in HSTRETCH.items():
    for _cr in _cells:
        _HSTRETCH_MAP[_cr] = _pid

# ── Constantes de estilo ─────────────────────────────────────────────────────
# ── Constantes de estilo ─────────────────────────────────────────────────────
_INK          = (52, 42, 76)
_BOARD_BG     = (238, 230, 218)  # Fundo tom de areia/biscoito (quente e aconchegante)
_BOARD_SH     = (38,  28, 62)
_PATH_1       = (255, 252, 245)  # Casinha clara (creme)
_PATH_2       = (245, 238, 225)  # Casinha escura (baunilha)


# ── Constantes de estilo ─────────────────────────────────────────────────────
_INK          = (52, 42, 76)
_BOARD_BG     = (238, 230, 218)  # Fundo areia
_PATH_1       = (255, 255, 255)  # Branco puro para destacar
_PATH_2       = (245, 238, 225)  # Bege bem clarinho para o xadrez
_NEUTRAL_SH   = (215, 205, 190)  # Sombra fixa: OBRIGATORIAMENTE mais escura que o fundo
_NEUTRAL_OUT  = (225, 215, 202)  # Bordinha fixa para separar do fundo

def _sh(color, amt=45):
    """Cor de sombra flat — escurece sem alpha."""
    return (max(color[0]-amt, 0), max(color[1]-amt, 0), max(color[2]-amt, 0))

# ── Primitivos ───────────────────────────────────────────────────────────────
def _cell_rect(col, row, margin):
    from constants import BX, BY, CELL
    return pygame.Rect(
        BX + col * CELL + margin,
        BY + row * CELL + margin,
        CELL - margin * 2,
        CELL - margin * 2,
    )

def _draw_cell(surf, fill, col, row, *, margin=2, radius=9):
    """Células com sombras e bordas corrigidas para garantir contraste."""
    rect = _cell_rect(col, row, margin)
    
    # 1. Definição de Cores
    if fill in (_PATH_1, _PATH_2):
        # Usamos as cores fixas que garantem contraste contra o fundo de areia
        sh_color = _NEUTRAL_SH
        border_color = _NEUTRAL_OUT
    else:
        # Casas coloridas continuam calculando a própria sombra
        sh_color = _sh(fill, 35)
        border_color = _sh(fill, 20)

    # 2. Sombra deslocada
    sh_rect = rect.move(0, 3)
    pygame.draw.rect(surf, sh_color, sh_rect, border_radius=radius)
    
    # 3. Corpo Principal
    pygame.draw.rect(surf, fill, rect, border_radius=radius)
    
    # 4. Borda Fina de Contorno
    pygame.draw.rect(surf, border_color, rect, 2, border_radius=radius)


def _fat_star(surf, fill, cx, cy, r_out=14, r_in=6, points=5):
    """Estrela nítida: sombra quente flutuante + contorno fino + highlight transparente."""
    n = points * 2
    verts = []
    
    for i in range(n):
        a = math.pi / points * i - math.pi / 2
        r = r_out if i % 2 == 0 else r_in
        verts.append((cx + r * math.cos(a), cy + r * math.sin(a)))

    if fill == (255, 212, 24):
        body_color = (255, 225, 20)
        edge_color = (230, 140, 0)
    else:
        body_color = fill
        edge_color = _sh(fill, 40)

    surf_size = int(r_out * 2 + 16)
    local_cx = surf_size // 2
    local_cy = surf_size // 2

    # 1. SOMBRA FLUTUANTE 
    sh_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    local_verts = []
    for i in range(n):
        a = math.pi / points * i - math.pi / 2
        r = r_out if i % 2 == 0 else r_in
        local_verts.append((local_cx + r * math.cos(a), local_cy + r * math.sin(a)))
    
    pygame.draw.polygon(sh_surf, (50, 20, 0, 20), [(x, y + 4) for x, y in local_verts])
    pygame.draw.polygon(sh_surf, (50, 20, 0, 40), [(x, y + 2) for x, y in local_verts])
    surf.blit(sh_surf, (cx - local_cx, cy - local_cy))

    # 2. CONTORNO FINO
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        pygame.draw.polygon(surf, edge_color, [(x + dx, y + dy) for x, y in verts])

    # 3. CORPO PRINCIPAL
    pygame.draw.polygon(surf, body_color, verts)

    # 4. HIGHLIGHT SUAVE E TRANSPARENTE
    # Superfície invisível para o brilho
    hl_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    hl_verts = []
    for i in range(n):
        a = math.pi / points * i - math.pi / 2
        r = (r_out * 0.75) if i % 2 == 0 else (r_in * 0.75)
        # Usamos as coordenadas locais da superfície transparente
        hl_verts.append((local_cx + r * math.cos(a) - 1, local_cy + r * math.sin(a) - 1))

    hl_path = [hl_verts[8], hl_verts[9], hl_verts[0], hl_verts[1]]
    thick = 3 if r_out > 15 else 2 
    
    # Desenhamos com (255, 255, 255, 130) -> Branco com ~50% de opacidade
    pygame.draw.lines(hl_surf, (255, 255, 255, 130), False, hl_path, thick)
    
    # Carimbamos o brilho transparente por cima
    surf.blit(hl_surf, (cx - local_cx, cy - local_cy))


# ── Tabuleiro principal ──────────────────────────────────────────────────────
def draw_board(surf: pygame.Surface):

   # 1 · Fundo ────────────────────────────────────────────────────────────────
    PAD = 15

    bg_rect = pygame.Rect(BX - PAD, BY - PAD, BSIZE + PAD*2, BSIZE + PAD*2)

    # Sombra do fundo (agora centralizada e esfumaçada para todos os lados)
    sh_bg = pygame.Surface((bg_rect.width + 24, bg_rect.height + 24), pygame.SRCALPHA)
    pygame.draw.rect(sh_bg, (0, 0, 0, 10), (0, 0, bg_rect.width + 24, bg_rect.height + 24), border_radius=32)
    pygame.draw.rect(sh_bg, (0, 0, 0, 15), (6, 6, bg_rect.width + 12, bg_rect.height + 12), border_radius=28)
    surf.blit(sh_bg, (bg_rect.x - 12, bg_rect.y - 12))

    # Fundo branco puro
    pygame.draw.rect(surf, _BOARD_BG, bg_rect, border_radius=28)
    
    # NOVA BORDA: Linha de contorno tom-sobre-tom para separar o tabuleiro do menu
    pygame.draw.rect(surf, (215, 210, 200), bg_rect, 4, border_radius=28)

    # 2 · Zonas home (cantos 6×6) ──────────────────────────────────────────────
    _home_origins = {0: (0, 0), 1: (9, 0), 2: (9, 9), 3: (0, 9)}

    for pid, (oc, or_) in _home_origins.items():
        sz = CELL * 5.9
        
        # Calcula quanto espaço sobrou das 6 células originais (o respiro)
        sobra = CELL * 6 - sz
        
        # Empurra para as extremidades (quinas do tabuleiro)
        offset_x = sobra if oc == 9 else 0
        offset_y = sobra if or_ == 9 else 0

        px = BX + oc * CELL + offset_x
        py = BY + or_ * CELL + offset_y

        # 1. SOMBRA BASE CENTRALIZADA
        sh_sz = int(sz + 20)
        sh_surf = pygame.Surface((sh_sz, sh_sz), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (0, 0, 0, 6),  (0, 0, sh_sz, sh_sz), border_radius=32)
        pygame.draw.rect(sh_surf, (0, 0, 0, 10), (3, 3, sh_sz - 6, sh_sz - 6), border_radius=30)
        pygame.draw.rect(sh_surf, (0, 0, 0, 15), (7, 7, sh_sz - 14, sh_sz - 14), border_radius=28)
        surf.blit(sh_surf, (px - 10, py - 10))

        # 2. CORPO DA BASE 
        pygame.draw.rect(surf, PC[pid], (px, py, sz, sz), border_radius=26)

        # 3. YARD (Área Branca Central)
        inner_sz = CELL * 4.4
        pad = (sz - inner_sz) / 2
        
        sh_inner = pygame.Surface((inner_sz + 8, inner_sz + 8), pygame.SRCALPHA)
        pygame.draw.rect(sh_inner, (0, 0, 0, 15), (3, 3, inner_sz, inner_sz), border_radius=18)
        surf.blit(sh_inner, (px + pad, py + pad))

        pygame.draw.rect(surf, WHITE, (px + pad, py + pad, inner_sz, inner_sz), border_radius=18)

        # 4. SPOTS (Buracos redondinhos)
        cx_base = px + sz / 2
        cy_base = py + sz / 2
        
        spread = 1.05 
        
        for dr in [-1, 1]:
            for dc in [-1, 1]:
                cx_ = cx_base + dc * spread * CELL
                cy_ = cy_base + dr * spread * CELL
                
                # O meio-termo perfeito: aumentamos de 0.65 para 0.73
                r = int(CELL * 0.73) 

                pygame.draw.circle(surf, _sh(WHITE, 20), (cx_ + 2, cy_ + 2), r)
                pygame.draw.circle(surf, PL[pid], (cx_, cy_), r)
                
                hl_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                hr = r - 2 
                pygame.draw.circle(hl_surf, (255, 255, 255, 140), (r, r), hr)
                
                mask = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                mask.fill((255, 255, 255, 255)) 
                
                pygame.draw.circle(mask, (0, 0, 0, 0), (r + 2, r + 2), hr)
                
                hl_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                surf.blit(hl_surf, (cx_ - r, cy_ - r))


    # 3 · Casas do caminho principal ───────────────────────────────────────────
    _PM = 3   
    _PR = 9   

    # Usamos enumerate(MPATH) para pegar o índice (idx) e criar o padrão xadrez
    for idx, (c, r) in enumerate(MPATH):
        if (c, r) in _ENTRY_CELLS:
            pid  = _ENTRY_CELLS[(c, r)]
            fill = PC[pid]
        else:
            # Padrão xadrez suave: se for par usa Creme, se for ímpar usa Baunilha
            fill = _PATH_1 if idx % 2 == 0 else _PATH_2
            
        _draw_cell(surf, fill, c, r, margin=_PM, radius=_PR)

    # 4 · Corredor de chegada ──────────────────────────────────────────────────
    for (c, r), pid in _HSTRETCH_MAP.items():
        _draw_cell(surf, PC[pid], c, r, margin=_PM, radius=_PR)

    # 5 · Centro 3×3 ───────────────────────────────────────────────────────────
    ox  = BX + 6 * CELL
    oy  = BY + 6 * CELL
    cs  = CELL * 3
    
    # Coordenadas locais para a superfície temporária
    mid_local = (cs // 2, cs // 2)
    corners_local = [
        (0,  0),
        (cs, 0),
        (cs, cs),
        (0,  cs),
    ]

    # Sombra sob o miolo central flutuante
    sh_center = pygame.Surface((cs + 8, cs + 8), pygame.SRCALPHA)
    pygame.draw.rect(sh_center, (0, 0, 0, 12), (3, 5, cs, cs), border_radius=16)
    surf.blit(sh_center, (ox, oy))

    # Truque da Máscara: Criamos uma superfície transparente só para o centro
    center_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)

    # Desenhamos os triângulos nessa superfície
    for i, pid in enumerate([0, 1, 2, 3]):
        pygame.draw.polygon(center_surf, PC[pid], [corners_local[i], corners_local[(i + 1) % 4], mid_local])

    # Criamos a máscara arredondada (tudo que for branco aqui vai aparecer)
    mask = pygame.Surface((cs, cs), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, cs, cs), border_radius=16)

    # BLEND_RGBA_MIN corta as pontas quadradas dos triângulos usando a máscara!
    center_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

    # Agora sim, colamos o centro perfeito e arredondado no tabuleiro
    surf.blit(center_surf, (ox, oy))

    # Estrela central grande (desenhada por cima, baseada na posição global)
    mid_global = (ox + cs // 2, oy + cs // 2)
    _fat_star(surf, (255, 212, 24), mid_global[0], mid_global[1] - 2, r_out=22, r_in=10, points=5)

    # 6 · Estrelas nas casas seguras ────────────────────────────────────────────
    for c, r in SAFE:
        if (c, r) not in _ENTRY_CELLS:
            cx_ = BX + c * CELL + CELL // 2
            cy_ = BY + r * CELL + CELL // 2
            # Movemos 1px pra cima para compensar a sombrinha
            _fat_star(surf, (255, 212, 24), cx_, cy_ - 1, r_out=10, r_in=5, points=5)
