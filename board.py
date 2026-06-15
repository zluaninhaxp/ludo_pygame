"""
board.py — Tabuleiro estilo cute / flat-vector / sticker.
Usa constants via módulo para suportar redimensionamento dinâmico.
"""
import pygame
import math
import constants as C
from constants import WHITE, CREAM, PC, PL, PD

# ── Constantes de estilo (fixas, sem dependência de CELL) ──────────────────
_INK        = (52,  42,  76)
_BOARD_BG   = (238, 230, 218)
_PATH_1     = (255, 255, 255)
_PATH_2     = (245, 238, 225)
_NEUTRAL_SH = (215, 205, 190)
_NEUTRAL_OUT= (225, 215, 202)

def _sh(color, amt=45):
    return (max(color[0]-amt, 0), max(color[1]-amt, 0), max(color[2]-amt, 0))


# ── Lookup maps (reconstruídos a cada draw para refletir update_layout) ────
def _build_lookups():
    entry_cells  = {C.MPATH[v]: k for k, v in C.ENTRY.items()}
    hstretch_map = {}
    for pid, cells in C.HSTRETCH.items():
        for cr in cells:
            hstretch_map[cr] = pid
    return entry_cells, hstretch_map


# ── Primitivos ────────────────────────────────────────────────────────────────
def _cell_rect(col, row, margin):
    return pygame.Rect(
        C.BX + col * C.CELL + margin,
        C.BY + row * C.CELL + margin,
        C.CELL - margin * 2,
        C.CELL - margin * 2,
    )

def _draw_cell(surf, fill, col, row, *, margin=2, radius=9):
    rect = _cell_rect(col, row, margin)
    if fill in (_PATH_1, _PATH_2):
        sh_color     = _NEUTRAL_SH
        border_color = _NEUTRAL_OUT
    else:
        sh_color     = _sh(fill, 35)
        border_color = _sh(fill, 20)
    sh_rect = rect.move(0, 3)
    pygame.draw.rect(surf, sh_color,     sh_rect, border_radius=radius)
    pygame.draw.rect(surf, fill,         rect,    border_radius=radius)
    pygame.draw.rect(surf, border_color, rect, 2, border_radius=radius)


def _fat_star(surf, fill, cx, cy, r_out=14, r_in=6, points=5):
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

    surf_size  = int(r_out * 2 + 16)
    local_cx   = surf_size // 2
    local_cy   = surf_size // 2

    sh_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    local_verts = []
    for i in range(n):
        a = math.pi / points * i - math.pi / 2
        r = r_out if i % 2 == 0 else r_in
        local_verts.append((local_cx + r * math.cos(a), local_cy + r * math.sin(a)))
    pygame.draw.polygon(sh_surf, (50, 20, 0, 20), [(x, y + 4) for x, y in local_verts])
    pygame.draw.polygon(sh_surf, (50, 20, 0, 40), [(x, y + 2) for x, y in local_verts])
    surf.blit(sh_surf, (cx - local_cx, cy - local_cy))

    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        pygame.draw.polygon(surf, edge_color, [(x + dx, y + dy) for x, y in verts])
    pygame.draw.polygon(surf, body_color, verts)

    hl_surf  = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    hl_verts = []
    for i in range(n):
        a = math.pi / points * i - math.pi / 2
        r = (r_out * 0.75) if i % 2 == 0 else (r_in * 0.75)
        hl_verts.append((local_cx + r * math.cos(a) - 1, local_cy + r * math.sin(a) - 1))
    hl_path = [hl_verts[8], hl_verts[9], hl_verts[0], hl_verts[1]]
    thick   = 3 if r_out > 15 else 2
    pygame.draw.lines(hl_surf, (255, 255, 255, 130), False, hl_path, thick)
    surf.blit(hl_surf, (cx - local_cx, cy - local_cy))


# ── Tabuleiro principal ───────────────────────────────────────────────────────
def draw_board(surf: pygame.Surface):
    ENTRY_CELLS, HSTRETCH_MAP = _build_lookups()
    CELL  = C.CELL
    BX    = C.BX
    BY    = C.BY
    BSIZE = C.BSIZE

    PAD    = max(8, CELL // 5)
    radius = max(6, CELL // 5)

    # 1 · Fundo ────────────────────────────────────────────────────────────────
    bg_rect = pygame.Rect(BX - PAD, BY - PAD, BSIZE + PAD*2, BSIZE + PAD*2)

    sh_bg = pygame.Surface((bg_rect.width + 24, bg_rect.height + 24), pygame.SRCALPHA)
    pygame.draw.rect(sh_bg, (0, 0, 0, 10), (0, 0, bg_rect.width+24, bg_rect.height+24), border_radius=32)
    pygame.draw.rect(sh_bg, (0, 0, 0, 15), (6, 6, bg_rect.width+12, bg_rect.height+12), border_radius=28)
    surf.blit(sh_bg, (bg_rect.x - 12, bg_rect.y - 12))

    pygame.draw.rect(surf, _BOARD_BG, bg_rect, border_radius=28)
    pygame.draw.rect(surf, (215, 210, 200), bg_rect, 4, border_radius=28)

    # 2 · Zonas home ──────────────────────────────────────────────────────────
    for pid, (oc, or_) in {0:(0,0), 1:(9,0), 2:(9,9), 3:(0,9)}.items():
        sz    = CELL * 5.9
        sobra = CELL * 6 - sz
        offset_x = sobra if oc == 9 else 0
        offset_y = sobra if or_ == 9 else 0
        px = BX + oc * CELL + offset_x
        py = BY + or_ * CELL + offset_y

        sh_sz   = int(sz + 20)
        sh_surf = pygame.Surface((sh_sz, sh_sz), pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (0,0,0, 6),  (0,0,sh_sz,sh_sz), border_radius=32)
        pygame.draw.rect(sh_surf, (0,0,0,10),  (3,3,sh_sz-6,sh_sz-6), border_radius=30)
        pygame.draw.rect(sh_surf, (0,0,0,15),  (7,7,sh_sz-14,sh_sz-14), border_radius=28)
        surf.blit(sh_surf, (px - 10, py - 10))

        pygame.draw.rect(surf, PC[pid], (px, py, sz, sz), border_radius=26)

        inner_sz = CELL * 4.4
        pad_i    = (sz - inner_sz) / 2
        sh_in    = pygame.Surface((inner_sz+8, inner_sz+8), pygame.SRCALPHA)
        pygame.draw.rect(sh_in, (0,0,0,15), (3,3,inner_sz,inner_sz), border_radius=18)
        surf.blit(sh_in, (px + pad_i, py + pad_i))
        pygame.draw.rect(surf, WHITE, (px + pad_i, py + pad_i, inner_sz, inner_sz), border_radius=18)

        cx_base = px + sz / 2
        cy_base = py + sz / 2
        spread  = 1.05
        for dr in [-1, 1]:
            for dc in [-1, 1]:
                cx_ = cx_base + dc * spread * CELL
                cy_ = cy_base + dr * spread * CELL
                r   = int(CELL * 0.73)
                pygame.draw.circle(surf, _sh(WHITE, 20), (cx_ + 2, cy_ + 2), r)
                pygame.draw.circle(surf, PL[pid], (cx_, cy_), r)

                hl_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                hr = r - 2
                pygame.draw.circle(hl_surf, (255,255,255,140), (r, r), hr)
                mask = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                mask.fill((255,255,255,255))
                pygame.draw.circle(mask, (0,0,0,0), (r+2, r+2), hr)
                hl_surf.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)

    # 3 · Caminho principal ────────────────────────────────────────────────────
    _PM = max(2, CELL // 15)
    _PR = max(6, CELL // 5)
    for idx, (col, row) in enumerate(C.MPATH):
        if (col, row) in ENTRY_CELLS:
            fill = PC[ENTRY_CELLS[(col, row)]]
        else:
            fill = _PATH_1 if idx % 2 == 0 else _PATH_2
        _draw_cell(surf, fill, col, row, margin=_PM, radius=_PR)

    # 4 · Corredor de chegada ──────────────────────────────────────────────────
    for (col, row), pid in HSTRETCH_MAP.items():
        _draw_cell(surf, PC[pid], col, row, margin=_PM, radius=_PR)

    # 5 · Centro 3×3 ───────────────────────────────────────────────────────────
    ox = BX + 6 * CELL
    oy = BY + 6 * CELL
    cs = CELL * 3

    sh_center = pygame.Surface((cs + 8, cs + 8), pygame.SRCALPHA)
    pygame.draw.rect(sh_center, (0,0,0,12), (3, 5, cs, cs), border_radius=16)
    surf.blit(sh_center, (ox, oy))

    center_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
    mid_l = (cs // 2, cs // 2)
    corners_l = [(0,0),(cs,0),(cs,cs),(0,cs)]
    for i, pid in enumerate([1, 2, 3, 0]):
        pygame.draw.polygon(center_surf, PC[pid],
                            [corners_l[i], corners_l[(i+1)%4], mid_l])
    mask = pygame.Surface((cs, cs), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255,255,255,255), (0,0,cs,cs), border_radius=16)
    center_surf.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(center_surf, (ox, oy))

    # --- TROCA DA ESTRELA PELO TROFÉU ---
    import os
    try:
        # Carrega e escala o troféu proporcionalmente ao tamanho do centro
        trofeu_path = os.path.join("images", "trofeu.png")
        trofeu_img = pygame.image.load(trofeu_path).convert_alpha()
        
        # O troféu ocupará 75% do tamanho do quadrado central (cs)
        t_size = int(cs * 0.9)
        trofeu_img = pygame.transform.smoothscale(trofeu_img, (t_size, t_size))
        
        # Calcula posição central
        t_rect = trofeu_img.get_rect(center=(ox + cs//2, oy + cs//2))
        
        surf.blit(trofeu_img, t_rect)
    except Exception as e:
        # Fallback caso a imagem não seja encontrada
        print(f"Erro ao carregar trofeu.png: {e}")
        r_out = max(10, CELL // 2)
        r_in  = max(4,  CELL // 4)
        _fat_star(surf, (255, 212, 24),
                  ox + cs//2, oy + cs//2 - 2,
                  r_out=r_out, r_in=r_in, points=5)

    # 6 · Estrelas nas casas seguras ──────────────────────────────────────────
    r_s_out = max(6, CELL // 4)
    r_s_in  = max(3, CELL // 8)
    for col, row in C.SAFE:
        if (col, row) not in ENTRY_CELLS:
            cx_ = BX + col * CELL + CELL // 2
            cy_ = BY + row * CELL + CELL // 2
            _fat_star(surf, (255,212,24), cx_, cy_-1,
                      r_out=r_s_out, r_in=r_s_in, points=5)