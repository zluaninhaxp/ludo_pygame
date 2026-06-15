"""
renderer.py — Peças, dado, HUD flutuante e telas de fim.
"""
import pygame
import math
import os
import constants as C

WHITE = C.WHITE
BLACK = C.BLACK
BG    = C.BG
PC    = C.PC
PL    = C.PL
PD    = C.PD
PN    = C.PN

pygame.font.init()
_font_cache = {}

def _load_font(size, bold=False):
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    for name in ("Fredoka One", "Nunito", "Varela Round",
                 "Comic Sans MS", "Arial Rounded MT Bold"):
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            _font_cache[key] = f
            return f
        except Exception:
            pass
    f = pygame.font.SysFont("Arial", size, bold=bold)
    _font_cache[key] = f
    return f

def _fonts(card_w):
    base = max(10, card_w // 10)
    return (
        _load_font(int(base * 3.0), bold=True),
        _load_font(int(base * 1.6), bold=True),
        _load_font(int(base * 1.2), bold=True),
        _load_font(int(base * 0.95)),
    )

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
    return (max(color[0]-amt,0), max(color[1]-amt,0), max(color[2]-amt,0))

def _txt(surf, text, font, color, cx, cy, anchor="c"):
    img = font.render(str(text), True, color)
    r   = img.get_rect()
    if   anchor == "c":  r.center  = (cx, cy)
    elif anchor == "tl": r.topleft = (cx, cy)
    elif anchor == "tc": r.midtop  = (cx, cy)
    surf.blit(img, r)

def _txt_sh(surf, text, font, color, cx, cy, sh_col=None, off=2, anchor="c"):
    sc = sh_col or _sh(color, 90)
    _txt(surf, text, font, sc,    cx+off, cy+off, anchor)
    _txt(surf, text, font, color, cx,     cy, anchor)

_DIE_DOTS = {
    1: [(0,0)],
    2: [(-1,-1),(1,1)],
    3: [(-1,-1),(0,0),(1,1)],
    4: [(-1,-1),(1,-1),(-1,1),(1,1)],
    5: [(-1,-1),(1,-1),(0,0),(-1,1),(1,1)],
    6: [(-1,-1),(1,-1),(-1,0),(1,0),(-1,1),(1,1)],
}

def draw_die(surf, val, spinning, cx, cy, size=56):
    rad   = max(6, size // 5)
    face  = (255, 250, 238) if not spinning else (255, 234, 176)
    border= (92,  74, 152)  if not spinning else (235, 162,  28)
    rect  = pygame.Rect(cx - size//2, cy - size//2, size, size)
    pygame.draw.rect(surf, face,   rect, border_radius=rad)
    pygame.draw.rect(surf, border, rect, 3, border_radius=rad)
    pygame.draw.rect(surf, _INK,   rect, 1, border_radius=rad)

    dot_fill = (212, 42, 68) if spinning else (46, 36, 72)
    dot_sh   = _sh(dot_fill, 55)
    step     = max(6, size // 8)
    r_dot    = max(3, size // 11)
    for dx, dy in _DIE_DOTS.get(val, []):
        px_ = cx + dx * step
        py_ = cy + dy * step
        pygame.draw.circle(surf, dot_sh,  (px_+1, py_+1), r_dot)
        pygame.draw.circle(surf, dot_fill,(px_,   py_),    r_dot)

_PIECE_IMAGES = {}

def _get_piece_image(nome, max_size):
    key = (nome, max_size)
    if key in _PIECE_IMAGES:
        return _PIECE_IMAGES[key]
    final = pygame.Surface((max_size, max_size), pygame.SRCALPHA)
    path  = os.path.join("images", f"{nome}.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        ow, oh = img.get_size()
        scale  = min(max_size / ow, max_size / oh)
        nw, nh = int(ow * scale), int(oh * scale)
        img = pygame.transform.smoothscale(img, (nw, nh))
        final.blit(img, ((max_size-nw)//2, (max_size-nh)//2))
    except Exception:
        pass
    _PIECE_IMAGES[key] = final
    return final

_OFFSETS4 = [(-6, -6), (6, -6), (-6, 6), (6, 6)]

def draw_pieces(surf, game):
    cell_cnt = {}
    for pl in game.players:
        for p in pl.pieces:
            if p.state == "active" and p.grid:
                cell_cnt[p.grid] = cell_cnt.get(p.grid, 0) + 1
    cell_ord = {}

    anim_p = game.anim_piece
    astep  = (min(game.anim_step, len(game.anim_path)-1)
              if game.anim_path else 0)

    for pl in game.players:
        for p in pl.pieces:
            if p.state == "done":
                continue
            
            is_anim = (p is anim_p and game.anim_path)
            bounce_off = 0
            
            if is_anim:
                p0 = game.anim_path[astep]
                if astep + 1 < len(game.anim_path):
                    p1 = game.anim_path[astep + 1]
                else:
                    p1 = p0
                
                if game.phase == "anim_capture":
                    duration = 500.0  
                    jump_height = C.CELL * 3.5  
                else:
                    duration = 200.0  
                    jump_height = C.CELL * 0.4
                    
                progress = min(1.0, game.anim_timer / duration) 
                px = p0[0] + (p1[0] - p0[0]) * progress
                py = p0[1] + (p1[1] - p0[1]) * progress
                bounce_off = -math.sin(progress * math.pi) * jump_height
                
            elif p.state == "home":
                px, py = C.YARDS[p.pid][p.idx]
            elif p.state == "active":
                g = p.grid
                if g is None:
                    continue
                ox, oy = 0, 0
                if cell_cnt.get(g, 1) > 1:
                    k = cell_ord.get(g, 0)
                    cell_ord[g] = k + 1
                    ox, oy = _OFFSETS4[k % 4]
                bx, by = C.gpx(*g)
                px, py = bx + ox, by + oy
            else:
                continue
                
            sel = (p in game.movable and game.phase == "pick")
            _draw_piece(surf, p.pid, p.idx, px, py, sel, bounce_off)

    for p in getattr(game, 'particles', []):
        cx, cy, sx, sy, color, size, life = p
        w = max(1, int(size * abs(math.sin(life * 0.15))))
        h = size
        rect = pygame.Rect(cx - w//2, cy - h//2, w, h)
        pygame.draw.rect(surf, color, rect, border_radius=2)

def _draw_piece(surf, pid, idx, px, py, sel, bounce_off=0):
    max_size = int(C.CELL * 0.95)
    nome     = C.PLAYER_CHOICES.get(pid, "default")
    
    py_final = py + bounce_off
    img = _get_piece_image(nome, max_size)
    current_size = max_size

    if sel:
        pulse = (math.sin(pygame.time.get_ticks() * 0.003) + 1.0) / 2.0
        current_size = int(max_size * (1.0 + pulse * 0.12)) // 2 * 2
        img = pygame.transform.smoothscale(img, (current_size, current_size))

    img_rect = img.get_rect(center=(px, py_final))

    shadow_size = int(current_size * 1.1)
    if bounce_off < 0:
        shrink = int(bounce_off * 0.3)
        shadow_size = max(15, shadow_size + shrink)
        
    sh_surf = pygame.Surface((shadow_size, shadow_size), pygame.SRCALPHA)
    sh_img  = pygame.transform.smoothscale(img, (shadow_size, shadow_size))
    sh_surf.blit(sh_img, (0, 0))
    
    sh_alpha = max(10, int(40 + bounce_off * 0.6))
    sh_surf.fill((0, 0, 0, sh_alpha), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(sh_surf, (px - shadow_size // 2, py - shadow_size // 2))

    surf.blit(img, img_rect)

# ── HUD: 4 Cantos Flutuantes Alinhados às Bordas ──────────────────────────────
def draw_sidebar(surf, game):
    W = C.W
    H = C.H
    BX = C.BX
    BY = C.BY
    BSIZE = C.BSIZE

    lat_w = BX 
    card_w = max(110, min(220, int(lat_w * 0.82)))
    card_h = max(56, int(card_w * 0.45))
    die_size = max(32, int(card_w * 0.4))

    F_BIG, F_MED, F_SM, F_XSM = _fonts(card_w)

    gap = max(8, int(lat_w * 0.08))
    rx_left  = BX - gap - card_w
    rx_right = BX + BSIZE + gap

    # Alinhado exatamente no topo da base (RY)
    ry_top = BY
    ry_bot = BY + BSIZE - card_h

    act_pid = game.players[game.turn].pid if game.phase != "end" else -1

    anchors_rx = {0: rx_left, 1: rx_right, 2: rx_right, 3: rx_left}
    anchors_ry = {0: ry_top,  1: ry_top,   2: ry_bot,   3: ry_bot}

    for pl in game.players:
        pid = pl.pid
        rx = anchors_rx[pid]
        ry = anchors_ry[pid]
        
        cx = rx + card_w // 2
        cy = ry + card_h // 2
        act = (pid == act_pid)

        bg = PC[pid] if act else _CARD_IDLE

        pygame.draw.rect(surf, bg,        (rx, ry, card_w, card_h), border_radius=11)
        pygame.draw.rect(surf, _HINT_COL, (rx, ry, card_w, card_h), 3 if act else 0, border_radius=11)
        pygame.draw.rect(surf, _INK,      (rx, ry, card_w, card_h), 1, border_radius=11)

        display_name = C.PLAYER_DISPLAY_NAMES.get(pid, PN[pid])
        _txt(surf, display_name, F_SM,  WHITE, cx, ry + int(card_h*0.3))
        _txt(surf, "Humano" if pl.human else "CPU", F_XSM, (235,228,255) if act else _DIM, cx, ry + int(card_h*0.6))

        fin  = sum(1 for p in pl.pieces if p.state == "done")
        rp   = max(4, card_w // 24)
        pip_y = ry + int(card_h * 0.85)
        pip_spacing = max(12, (card_w - 20) // 4)
        start_x = cx - (1.5 * pip_spacing)
        for k in range(4):
            px_   = start_x + k * pip_spacing
            sh_c  = PD[pid] if k < fin else (18,12,38)
            body  = WHITE   if k < fin else PL[pid]
            edge  = PC[pid] if k < fin else (60,48,92)
            pygame.draw.circle(surf, sh_c, (px_+1, pip_y+1), rp)
            pygame.draw.circle(surf, body, (px_,   pip_y),   rp)
            pygame.draw.circle(surf, edge, (px_,   pip_y),   rp, max(1, rp//2))

        if act:
            direction = 1 if pid in (0, 1) else -1
            if direction == 1:
                dcy = ry + card_h + die_size // 2 + max(8, int(H*0.015))
            else:
                dcy = ry - die_size // 2 - max(8, int(H*0.015))

            spinning = game.dice_spin > 0
            val = game.dice_show if spinning else (game.roll if game.roll else game.dice_final)
            draw_die(surf, val, spinning, cx, dcy, size=die_size)

            cp = game.cp()
            hint = ""
            if game.phase == "roll" and cp.human and not spinning:
                hint = "ESPACO = rolar"
            elif game.phase == "pick":
                hint = "Clique na peca"
            elif not cp.human and game.phase in ("roll","aipick","anim", "anim_capture"):
                hint = "CPU pensando..."

            if hint:
                hh = max(20, int(card_h * 0.35))
                if direction == 1:
                    hy = dcy + die_size // 2 + hh // 2 + max(6, int(H*0.01))
                else:
                    hy = dcy - die_size // 2 - hh // 2 - max(6, int(H*0.01))
                
                rect_y = hy - hh // 2
                
                pygame.draw.rect(surf, _HINT_BG, (rx, rect_y, card_w, hh), border_radius=8)
                pygame.draw.rect(surf, _HINT_COL,(rx, rect_y, card_w, hh), 2, border_radius=8)
                _txt(surf, hint, F_XSM, _HINT_COL, cx, hy)

                if game.msg:
                    if direction == 1:
                        msg_y = rect_y + hh + 8
                    else:
                        msg_y = rect_y - 8
                    _wrap_text(surf, game.msg, F_XSM, (255,205,85), cx, msg_y, 22, direction)

def _wrap_text(surf, text, font, color, cx, y0, max_chars, direction=1):
    words = text.split()
    line, lines = "" , []
    for w in words:
        t = (line + " " + w).strip()
        if len(t) <= max_chars:
            line = t
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    lines = lines[-4:]
    if direction == -1:
        y0 = y0 - (len(lines) * 16)
    for li, l in enumerate(lines):
        _txt(surf, l, font, color, cx, y0 + li * 16)

def draw_end_screen(surf, game):
    W = C.W
    H = C.H
    base_w = max(150, min(240, int(W * 0.15)))
    F_BIG, F_MED, F_SM, F_XSM = _fonts(base_w)
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((18, 10, 48, 205))
    surf.blit(ov, (0, 0))
    pw = max(320, int(W * 0.44))
    ph = max(280, int(H * 0.52))
    px = W//2 - pw//2
    py = H//2 - ph//2 - 10
    pygame.draw.rect(surf, (46,34,84),  (px,py,pw,ph), border_radius=18)
    pygame.draw.rect(surf, _HINT_COL,   (px,py,pw,ph), 4, border_radius=18)
    pygame.draw.rect(surf, _INK,        (px,py,pw,ph), 1, border_radius=18)
    _txt_sh(surf, "FIM DE JOGO!", F_BIG, _HINT_COL, W//2, py + int(ph*0.12))
    mcols = [_RANK_GOLD, _RANK_SILVER, _RANK_BRONZE, (150,150,150)]
    lbls  = ["1o lugar","2o lugar","3o lugar","4o lugar"]
    row_h = int(ph * 0.16)
    for ri, pid in enumerate(game.rankings):
        row_y = py + int(ph*0.27) + ri * row_h
        plw   = int(pw * 0.75)
        plh   = int(row_h * 0.72)
        plx   = W//2 - plw//2
        pygame.draw.rect(surf, PC[pid], (plx, row_y-plh//2, plw, plh), border_radius=10)
        pygame.draw.rect(surf, PD[pid], (plx, row_y-plh//2, plw, plh), 2, border_radius=10)
        pygame.draw.rect(surf, _INK,    (plx, row_y-plh//2, plw, plh), 1, border_radius=10)
        dname = C.PLAYER_DISPLAY_NAMES.get(pid, PN[pid])
        _txt_sh(surf, f"{lbls[min(ri,3)]}: {dname}", F_MED, WHITE, W//2, row_y+1)
    bw, bh = int(pw * 0.49), int(ph * 0.13)
    bx_ = W//2 - bw//2
    by_ = py + ph - bh - int(ph*0.06)
    pygame.draw.rect(surf, (10,68,10),  (bx_+3, by_+4, bw, bh), border_radius=12)
    pygame.draw.rect(surf, (50,168,50), (bx_,   by_,   bw, bh), border_radius=12)
    pygame.draw.rect(surf, (88,208,88), (bx_+6, by_+5, bw-12, bh//4), border_radius=7)
    pygame.draw.rect(surf, (28,118,28), (bx_,   by_,   bw, bh), 2, border_radius=12)
    pygame.draw.rect(surf, _INK,        (bx_,   by_,   bw, bh), 1, border_radius=12)
    _txt_sh(surf, "[R]  Reiniciar", F_MED, WHITE, W//2, by_ + bh//2 + 1)