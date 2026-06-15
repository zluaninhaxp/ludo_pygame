"""
renderer.py — Peças, dado, HUD flutuante estilizado e telas de fim.
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
                 "Comic Sans MS", "Arial Rounded MT Bold", "Arial"):
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
        _load_font(int(base * 1.3), bold=True),
        _load_font(int(base * 0.9)),
    )

_INK         = (52,  42,  76)
_HINT_COL    = (255, 222,  60)
_HINT_BG     = (62,  50,  98)
_DIM         = (145, 132, 178)
_RANK_GOLD   = (255, 208,   0)
_RANK_SILVER = (198, 198, 198)
_RANK_BRONZE = (190, 130,  50)

def _sh(color, amt=45):
    return (max(color[0]-amt,0), max(color[1]-amt,0), max(color[2]-amt,0))

def _txt(surf, text, font, color, cx, cy, anchor="c"):
    img = font.render(str(text), True, color)
    r   = img.get_rect()
    if   anchor == "c":  r.center  = (cx, cy)
    elif anchor == "tl": r.topleft = (cx, cy)
    elif anchor == "tc": r.midtop  = (cx, cy)
    elif anchor == "ml": r.midleft = (cx, cy)
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
    
    # --- MUDANÇA AQUI: Aumentamos o multiplicador para espalhar os pontos ---
    step     = max(8, int(size * 0.20))  # Antes era size // 8
    r_dot    = max(3, int(size * 0.11))  # Bolinhas um pouco mais gordinhas
    
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
        pulse_scale = 1.0 + abs(math.sin(pygame.time.get_ticks() * 0.004)) * 0.10
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


# ── HUD: Cards Premium Estilo Sticker ─────────────────────────────────────────
def draw_sidebar(surf, game):
    W = C.W
    H = C.H
    BX = C.BX
    BY = C.BY
    BSIZE = C.BSIZE

    lat_w = BX 
    card_w = max(130, min(240, int(lat_w * 0.85)))
    card_h = max(80, int(card_w * 0.65))
    head_h = int(card_h * 0.45) 
    
    die_size = max(24, int(card_w * 0.24))

    F_BIG, F_MED, F_SM, F_XSM = _fonts(card_w)

    gap = max(8, int(lat_w * 0.08))
    rx_left  = BX - gap - card_w
    rx_right = BX + BSIZE + gap

    ry_top = BY
    ry_bot = BY + BSIZE - card_h

    act_pid = game.players[game.turn].pid if game.phase != "end" else -1

    anchors_rx = {0: rx_left, 1: rx_right, 2: rx_right, 3: rx_left}
    anchors_ry = {0: ry_top,  1: ry_top,   2: ry_bot,   3: ry_bot}

    # ── PASSO 1: Desenhar o Painel do Dado (Animado) ──
    for pl in game.players:
        pid = pl.pid
        if pid != act_pid: continue
        
        rx = anchors_rx[pid]
        ry = anchors_ry[pid]
        cx = rx + card_w // 2  
        direction = 1 if pid in (0, 1) else -1
        
        panel_w = int(card_w * 0.45)
        panel_h = int(card_h * 0.60)
        px = rx + (card_w - panel_w) // 2
        
        if direction == 1:
            py = ry + card_h - 15
            die_cy = py + 15 + (panel_h - 15) // 2
        else:
            py = ry - panel_h + 15
            die_cy = py + (panel_h - 15) // 2

        scale = 1.0
        is_popping = (game.turn_ticks < 300 and not game.is_playing_again)
        is_pulsing = (game.is_playing_again and game.phase == "roll" and game.dice_spin == 0)

        if is_popping:
            progress = game.turn_ticks / 300.0
            scale = (1.0 - math.pow(1.0 - progress, 3)) + math.sin(progress * math.pi) * 0.15
        elif is_pulsing:
            pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1.0) / 2.0
            scale = 1.0 + pulse * 0.12

        current_die_sz  = max(4, int(die_size * scale)) // 2 * 2

        game.dice_rect = pygame.Rect(px, py, panel_w, panel_h)

        pygame.draw.rect(surf, (0,0,0,30), (px+4, py+4, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(surf, (100, 85, 115), game.dice_rect, border_radius=12)
        pygame.draw.rect(surf, _INK, game.dice_rect, 2, border_radius=12)

        spinning = game.dice_spin > 0
        val = game.dice_show if spinning else (game.roll if game.roll else game.dice_final)
        
        draw_die(surf, val, spinning, px + panel_w//2, die_cy, size=current_die_sz)

        cp = game.cp()
        hint = ""
        if game.phase == "roll" and cp.human and not spinning:
            # Se for turno extra (dado pulsando), muda o texto!
            if getattr(game, 'is_playing_again', False):
                hint = "Jogue novamente!"
            else:
                hint = "Clique = rolar"
        elif game.phase == "pick":
            hint = "Mova a peca"
        elif not cp.human and game.phase in ("roll","aipick","anim", "anim_capture"):
            hint = "CPU jogando..."

        if hint:
            # Posicionamento simples do texto, sem caixas de fundo
            if direction == 1:
                hy = py + panel_h + 14
            else:
                hy = py - 14
            
            # Texto limpo sem sombra
            _txt(surf, hint, F_XSM, (190, 180, 200), cx, hy)

            if game.msg:
                if direction == 1:
                    msg_y = hy + 18
                else:
                    msg_y = hy - 18
                _wrap_text(surf, game.msg, F_XSM, (210, 200, 220), cx, msg_y, 22, direction)

    # ── PASSO 2: Desenhar os Cards dos Jogadores por Cima ──
    for pl in game.players:
        pid = pl.pid
        rx = anchors_rx[pid]
        ry = anchors_ry[pid]
        cx = rx + card_w // 2  
        act = (pid == act_pid)

        pygame.draw.rect(surf, (0,0,0,30), (rx+5, ry+5, card_w, card_h), border_radius=16)
        
        body_col = (70, 56, 85) if act else (54, 42, 70)
        pygame.draw.rect(surf, body_col, (rx, ry, card_w, card_h), border_radius=16)
        
        pygame.draw.rect(surf, PC[pid], (rx, ry, card_w, head_h), border_top_left_radius=16, border_top_right_radius=16)
        
        pygame.draw.line(surf, _sh(PC[pid], 40), (rx, ry + head_h), (rx + card_w - 1, ry + head_h), 2)
        
        pygame.draw.rect(surf, _INK, (rx, ry, card_w, card_h), 2, border_radius=16)
        if act:
            pygame.draw.rect(surf, _HINT_COL, (rx-2, ry-2, card_w+4, card_h+4), 3, border_radius=18)

        avatar_sz = int(card_h * 0.55)
        avatar_x = rx + 10 + avatar_sz//2
        avatar_y = ry + head_h - int(avatar_sz * 0.15)
        
        pygame.draw.circle(surf, _sh(PC[pid], 30), (avatar_x, avatar_y+2), avatar_sz//2 + 2)
        pygame.draw.circle(surf, PC[pid], (avatar_x, avatar_y), avatar_sz//2 + 2) 
        
        nome = C.PLAYER_CHOICES.get(pid, "default")
        avatar_img = _get_piece_image(nome, avatar_sz)
        surf.blit(avatar_img, avatar_img.get_rect(center=(avatar_x, avatar_y)))

        name_x = rx + 15 + avatar_sz
        name_y = ry + head_h // 2
        display_name = C.PLAYER_DISPLAY_NAMES.get(pid, PN[pid])
        
        # Usando _txt no lugar de _txt_sh para remover a sombra
        _txt(surf, display_name, F_SM, WHITE, name_x, name_y, anchor="ml")
        
        type_y = ry + head_h + 12
        type_str = "Tipo: Humano" if pl.human else "Tipo: CPU"
        _txt(surf, type_str, F_XSM, (210, 200, 220), name_x, type_y, anchor="ml")

        fin = sum(1 for p in pl.pieces if p.state == "done")
        slot_r = max(6, int(card_w * 0.07))
        slot_spacing = (card_w - 20) / 4
        slot_start_x = rx + 10 + slot_spacing / 2
        slot_y = ry + card_h - slot_r - 10
        
        for k in range(4):
            sx = slot_start_x + k * slot_spacing
            
            pygame.draw.circle(surf, (30, 20, 40), (sx, slot_y+1), slot_r)
            pygame.draw.circle(surf, (40, 30, 55), (sx, slot_y), slot_r)
            pygame.draw.circle(surf, _INK, (sx, slot_y), slot_r, 1)
            
            if k < fin:
                pygame.draw.circle(surf, _sh(PL[pid], 30), (sx, slot_y+2), slot_r-2)
                pygame.draw.circle(surf, PL[pid], (sx, slot_y), slot_r-2)
                pygame.draw.circle(surf, PC[pid], (sx, slot_y), slot_r-2, 1)

# Nova versão do wrap_text que também usa sombrinha discreta (_txt_sh)
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
        # Removida a sombra aqui também, usando apenas _txt
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