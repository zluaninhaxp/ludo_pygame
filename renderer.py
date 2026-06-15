"""
renderer.py — Peças, dado, sidebar e telas de fim.
Usa import constants para sempre ler os valores atuais após resize().
"""
import pygame
import math
import os
import constants as C

# Paleta estática
WHITE = C.WHITE
BLACK = C.BLACK
BG    = C.BG
PC    = C.PC
PL    = C.PL
PD    = C.PD
PN    = C.PN

# ── Fontes (recriadas quando o layout muda) ───────────────────────────────────
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


def _fonts(side_w):
    """Retorna (F_BIG, F_MED, F_SM, F_XSM) proporcionais à sidebar."""
    base = max(10, side_w // 8)
    return (
        _load_font(int(base * 2.8), bold=True),
        _load_font(int(base * 1.8), bold=True),
        _load_font(int(base * 1.3), bold=True),
        _load_font(int(base * 1.0)),
    )


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
    return (max(color[0]-amt,0), max(color[1]-amt,0), max(color[2]-amt,0))


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
    _txt(surf, text, font, sc,    cx+off, cy+off)
    _txt(surf, text, font, color, cx,     cy)


# ── Dado ──────────────────────────────────────────────────────────────────────
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


# ── Gerenciador de Imagens ────────────────────────────────────────────────────
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


# Offsets para empilhar peças na mesma casa
_OFFSETS4 = [(-6, -6), (6, -6), (-6, 6), (6, 6)]

def draw_pieces(surf, game):
    import math # Garante que a matemática do pulo funcione
    
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
            bounce_off = 0 # Deslocamento vertical padrão
            
            if is_anim:
                # ── ANIMAÇÃO DESLIZANTE COM BOUNCE (PULO SUAVE) ──
                p0 = game.anim_path[astep]
                
                if astep + 1 < len(game.anim_path):
                    p1 = game.anim_path[astep + 1]
                else:
                    p1 = p0
                
                # O timer agora vai de 0 a 200 (mais lento e suave)
                progress = min(1.0, game.anim_timer / 200.0) 
                
                px = p0[0] + (p1[0] - p0[0]) * progress
                py = p0[1] + (p1[1] - p0[1]) * progress
                
                # Diminuímos a altura: agora o pulo é só 40% do tamanho da casa (era 70%)
                jump_height = C.CELL * 0.4 
                bounce_off = -math.sin(progress * math.pi) * jump_height
                
            elif p.state == "home":
                px, py = C.YARDS[p.pid][p.idx]
            elif p.state == "active":
                g = p.grid
                if g is None:
                    continue
                ox, oy = 0, 0
                # Empilha caso tenha mais de uma peça na casa
                if cell_cnt.get(g, 1) > 1:
                    k = cell_ord.get(g, 0)
                    cell_ord[g] = k + 1
                    ox, oy = _OFFSETS4[k % 4]
                bx, by = C.gpx(*g)
                px, py = bx + ox, by + oy
            else:
                continue
                
            sel = (p in game.movable and game.phase == "pick")
            
            # Passamos o px e py do CHÃO, e o bounce_off (ALTURA) separados
            _draw_piece(surf, p.pid, p.idx, px, py, sel, bounce_off)


def _draw_piece(surf, pid, idx, px, py, sel, bounce_off=0):
    import math
    max_size = int(C.CELL * 0.95)
    nome     = C.PLAYER_CHOICES.get(pid, "default")
    
    # A peça real vai subir, o resto (sombra) fica no chão
    py_final = py + bounce_off

    # 1. Carrega a imagem base (do tamanho normal)
    img = _get_piece_image(nome, max_size)
    current_size = max_size

    # 2. EFEITO PULSAR (Apenas se a peça puder ser jogada)
    # Removemos a bola dourada de fundo e aplicamos o zoom na própria imagem
    if sel:
        # Usamos abs() para a imagem apenas crescer e voltar ao normal (como um coração batendo)
        # O 0.15 significa que ela cresce até 15% do tamanho original
        pulse_scale = 1.0 + abs(math.sin(pygame.time.get_ticks() * 0.004)) * 0.15
        current_size = int(max_size * pulse_scale)
        
        # Estica a imagem suavemente para o tamanho do pulso
        img = pygame.transform.smoothscale(img, (current_size, current_size))

    img_rect = img.get_rect(center=(px, py_final))

    # 3. Sombra dinâmica (Acompanha o tamanho do pulso E a altura do pulo!)
    shadow_size = int(current_size * 1.1)
    
    if bounce_off < 0:
        shrink = int(bounce_off * 0.3)
        shadow_size = max(15, shadow_size + shrink)
        
    sh_surf = pygame.Surface((shadow_size, shadow_size), pygame.SRCALPHA)
    sh_img  = pygame.transform.smoothscale(img, (shadow_size, shadow_size))
    sh_surf.blit(sh_img, (0, 0))
    
    sh_alpha = max(10, int(40 + bounce_off * 0.6))
    sh_surf.fill((0, 0, 0, sh_alpha), special_flags=pygame.BLEND_RGBA_MULT)
    
    # Desenha a sombra encostada no chão
    surf.blit(sh_surf, (px - shadow_size // 2, py - shadow_size // 2))

    # 4. Desenha a peça voando ou pulsando
    surf.blit(img, img_rect)


# ── Sidebar ───────────────────────────────────────────────────────────────────
def draw_sidebar(surf, game):
    W      = C.W
    H      = C.H
    SIDE_W = C.SIDE_W

    F_BIG, F_MED, F_SM, F_XSM = _fonts(SIDE_W)

    sx = max(4, SIDE_W // 26)
    cw = SIDE_W - sx * 2
    ch = max(60, int(H * 0.105))

    pygame.draw.rect(surf, _PANEL_BG,   (0, 0, SIDE_W, H))
    pygame.draw.rect(surf, _PANEL_EDGE, (0, 0, SIDE_W, H), 3)

    title_y = max(28, int(H * 0.042))
    _txt_sh(surf, "LUDO", F_BIG, _HINT_COL, SIDE_W//2, title_y)

    card_start = title_y + max(28, int(H * 0.042))
    card_gap   = ch + max(6, int(H * 0.01))

    for i, pl in enumerate(game.players):
        y   = card_start + i * card_gap
        act = (i == game.turn and game.phase != "end")
        bg  = PC[pl.pid] if act else _CARD_IDLE

        pygame.draw.rect(surf, bg,        (sx, y, cw, ch), border_radius=11)
        pygame.draw.rect(surf, _HINT_COL, (sx, y, cw, ch), 3, border_radius=11)
        pygame.draw.rect(surf, _INK,      (sx, y, cw, ch), 1, border_radius=11)

        display_name = C.PLAYER_DISPLAY_NAMES.get(pl.pid, PN[pl.pid])
        _txt(surf, display_name, F_SM,  WHITE, SIDE_W//2, y + int(ch*0.25))
        _txt(surf,
             "Humano" if pl.human else "CPU",
             F_XSM,
             (235,228,255) if act else _DIM,
             SIDE_W//2, y + int(ch*0.5))

        fin  = sum(1 for p in pl.pieces if p.state == "done")
        rp   = max(5, SIDE_W // 24)
        pip_y = y + int(ch * 0.82)
        pip_spacing = max(18, (cw - sx*2) // 4)
        for k in range(4):
            cx_   = sx + rp + k * pip_spacing
            sh_c  = PD[pl.pid] if k < fin else (18,12,38)
            body  = WHITE      if k < fin else PL[pl.pid]
            edge  = PC[pl.pid] if k < fin else (60,48,92)
            pygame.draw.circle(surf, sh_c, (cx_+1, pip_y+2), rp)
            pygame.draw.circle(surf, body, (cx_,   pip_y),   rp)
            pygame.draw.circle(surf, edge, (cx_,   pip_y),   rp, 2)
            if k < fin:
                pygame.draw.circle(surf, _INK, (cx_, pip_y), rp, 1)

    # Placar
    if game.rankings:
        ry   = card_start + len(game.players) * card_gap + max(8, int(H*0.012))
        mcols= [_RANK_GOLD, _RANK_SILVER, _RANK_BRONZE, (148,148,148)]
        lbls = ["#1","#2","#3","#4"]
        _txt(surf, "Placar", F_XSM, _DIM, SIDE_W//2, ry)
        for ri, pid in enumerate(game.rankings):
            dname = C.PLAYER_DISPLAY_NAMES.get(pid, PN[pid])
            _txt(surf, f"{lbls[min(ri,3)]} {dname}",
                 F_XSM, mcols[min(ri,3)], SIDE_W//2, ry + int(H*0.026) + ri * int(H*0.026))

    # Dado
    die_size = max(36, int(SIDE_W * 0.55))
    dcx  = SIDE_W // 2
    dcy  = H - int(H * 0.22)
    spinning = game.dice_spin > 0
    val = game.dice_show if spinning else (game.roll if game.roll else game.dice_final)
    draw_die(surf, val, spinning, dcx, dcy, size=die_size)

    # Balão de dica
    cp   = game.cp()
    hint = ""
    if game.phase == "roll" and cp.human and not spinning:
        hint = "ESPACO = rolar"
    elif game.phase == "pick":
        hint = "Clique na peca"
    elif not cp.human and game.phase in ("roll","aipick","anim"):
        hint = "CPU pensando..."

    if hint:
        hw = SIDE_W - 12
        hx = 6
        hy = H - int(H * 0.135)
        hh = max(22, int(H * 0.038))
        pygame.draw.rect(surf, _HINT_BG, (hx, hy, hw, hh), border_radius=8)
        pygame.draw.rect(surf, _HINT_COL,(hx, hy, hw, hh), 2, border_radius=8)
        pygame.draw.rect(surf, _INK,     (hx, hy, hw, hh), 1, border_radius=8)
        _txt(surf, hint, F_XSM, _HINT_COL, SIDE_W//2, hy + hh//2)

    if game.msg:
        _wrap_text(surf, game.msg, F_XSM, (255,205,85), SIDE_W//2, H - int(H*0.085), 20)


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
    W = C.W
    H = C.H

    F_BIG, F_MED, F_SM, F_XSM = _fonts(C.SIDE_W)

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