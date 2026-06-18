"""
menu.py — Tela de configuração da partida.
Design Flat Premium "Fofinho" em Grid 2x2. Fonte Fredoka Ajustada.
"""
import pygame
import random
import constants as C
from piece import Player

pygame.font.init()
_font_cache = {}

def _load_font(size, bold=False):
    key = (size, bold)
    if key in _font_cache: 
        return _font_cache[key]
    
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(base_dir, "fonts", "Fredoka-Regular.ttf")
    
    try:
        f = pygame.font.Font(font_path, size)
        if bold: f.set_bold(True)
        _font_cache[key] = f
        return f
    except Exception as e:
        print(f"⚠️ Erro ao carregar a fonte Fredoka: {e}")
        for name in ("Fredoka One", "Fredoka", "Nunito", "Arial Rounded MT Bold", "Arial"):
            try:
                f = pygame.font.SysFont(name, size, bold=bold)
                _font_cache[key] = f
                return f
            except Exception: pass
                
    f = pygame.font.SysFont("Arial", size, bold=bold)
    _font_cache[key] = f
    return f

def _txt(surf, text, font, color, cx, cy, anchor="c"):
    img = font.render(str(text), True, color)
    r   = img.get_rect()
    if anchor == "c":    r.center   = (cx, cy)
    elif anchor == "tl": r.topleft  = (cx, cy)
    elif anchor == "ml": r.midleft  = (cx, cy)
    surf.blit(img, r)

def _sh(color, amt=45):
    r = max(0, min(255, color[0] - amt))
    g = max(0, min(255, color[1] - amt))
    b = max(0, min(255, color[2] - amt))
    return (r, g, b)

_CHAR_CACHE = {}

def _get_char_img(slug, size):
    # 1. Verifica se a imagem já foi carregada e processada neste tamanho
    key = (slug, size)
    if key in _CHAR_CACHE:
        return _CHAR_CACHE[key]
        
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    import os
    arquivo = "random" if slug is None else slug
    path = os.path.join("images", f"{arquivo}.png")
    
    try:
        # 2. Carrega e redimensiona (agora isso só vai acontecer UMA vez por imagem)
        img = pygame.image.load(path).convert_alpha()
        max_side = max(img.get_width(), img.get_height())
        scale = (size / max_side) * (0.65 if slug is None else 1.0)
        
        nw, nh = int(img.get_width() * scale), int(img.get_height() * scale)
        img = pygame.transform.smoothscale(img, (nw, nh))
        surf.blit(img, ((size - nw)//2, (size - nh)//2))
    except:
        pygame.draw.circle(surf, (80, 70, 110), (size//2, size//2), size//2 - 2)
        pygame.draw.circle(surf, (150, 140, 180), (size//2, size//2), size//2 - 2, 2)
        font = _load_font(int(size * 0.5), bold=True)
        texto_fallback = "?" if slug is None else "X"
        _txt(surf, texto_fallback, font, (255, 255, 255), size//2, size//2 - 2)
        
    # 3. Salva no cache antes de retornar
    _CHAR_CACHE[key] = surf
    return surf

_SHADOW_CACHE = {}

def _get_char_shadow(slug, size):
    key = (slug, size)
    if key in _SHADOW_CACHE:
        return _SHADOW_CACHE[key]
        
    img = _get_char_img(slug, size)
    shadow_size = int(size * 1.05)
    sh_img = pygame.transform.smoothscale(img, (shadow_size, shadow_size))
    sh_surf = pygame.Surface((shadow_size, shadow_size), pygame.SRCALPHA)
    sh_surf.blit(sh_img, (0, 0))
    sh_surf.fill((0, 0, 0, 90), special_flags=pygame.BLEND_RGBA_MULT)
    
    _SHADOW_CACHE[key] = sh_surf
    return sh_surf

class Menu:
    def __init__(self):
        self.n_players = 2
        self.types     = ["human", "cpu", "cpu", "cpu"]
        self.choices   = [None, None, None, None]
        self.screen    = "main"
        self.picker_slot = 0
        self.picker_scroll = 0
        self._hover = None

    def _L(self):
        W, H = C.W, C.H
        sc = min(W / 960, H / 720)
        # TAMANHOS AJUSTADOS (Levemente menores para acomodar a Fredoka)
        return dict(
            W=W, H=H, cx=W//2, sc=sc,
            F_BIG  = _load_font(max(20, int(35 * sc)), bold=True),
            F_MED  = _load_font(max(15, int(18 * sc)), bold=True),
            F_SM   = _load_font(max(12, int(16 * sc)), bold=True),
            F_XSM  = _load_font(max(10, int(13 * sc)), bold=True),
            F_XXSM = _load_font(max(9,  int(11 * sc)))
        )

    def _layout(self, L):
        W, H, cx, sc = L['W'], L['H'], L['cx'], L['sc']
        
        # Pílula de número de jogadores (Aumentada na largura)
        pill_w = max(280, int(320 * sc))
        pill_h = max(42,  int(50 * sc))
        pill_rect = pygame.Rect(cx - pill_w//2, int(110 * sc), pill_w, pill_h)
        
        btn_sz = int(34 * sc)
        btn_y  = pill_rect.centery - btn_sz // 2
        # Reposicionando os botões na direita da pílula
        rect_minus = pygame.Rect(pill_rect.right - btn_sz - int(8*sc), btn_y, btn_sz, btn_sz)
        rect_plus  = pygame.Rect(rect_minus.left - btn_sz - int(8*sc), btn_y, btn_sz, btn_sz)
        
        # Cards dos Jogadores
        card_w = max(280, int(320 * sc))
        card_h = max(125, int(145 * sc))
        gap_x  = int(30 * sc)
        gap_y  = int(25 * sc)
        
        start_y = int(180 * sc)
        
        cards = []
        for i in range(4):
            col = i % 2
            row = i // 2
            
            x = cx - card_w - gap_x//2 if col == 0 else cx + gap_x//2
            y = start_y + row * (card_h + gap_y)
            
            crect = pygame.Rect(x, y, card_w, card_h)
            
            btn_w = (card_w - int(30 * sc)) // 2
            btn_h = int(32 * sc)
            
            type_rect = pygame.Rect(crect.x + int(10*sc), crect.bottom - btn_h - int(10*sc), btn_w, btn_h)
            pick_rect = pygame.Rect(crect.right - int(10*sc) - btn_w, crect.bottom - btn_h - int(10*sc), btn_w, btn_h)
            cards.append((crect, type_rect, pick_rect))
            
        # Botão INICIAR (Mais largo)
        start_w = int(280 * sc)
        start_h = int(55 * sc)
        start_rect = pygame.Rect(cx - start_w//2, H - int(85 * sc), start_w, start_h)
        
        return pill_rect, rect_plus, rect_minus, cards, start_rect

    def draw(self, surf):
        L = self._L()
        surf.fill((36, 30, 60)) 
        
        self._draw_main(surf, L)
        
        if self.screen == "picker":
            self._draw_picker(surf, L)

    def _draw_main(self, surf, L):
        cx, sc = L['cx'], L['sc']
        pill_rect, rect_plus, rect_minus, cards, start_rect = self._layout(L)

        # Ajuste vertical fino (-2 ou -4) por causa do baseline da Fredoka
        _txt(surf, "LUDO", L['F_BIG'], (255, 210, 50), cx, int(45 * sc) - 2)
        _txt(surf, "Configuração da Partida", L['F_SM'], (150, 140, 180), cx, int(75 * sc) - 2)

        # PÍLULA: Alinhamento à ESQUERDA (ml) com margem para não encostar nos botões
        pygame.draw.rect(surf, (48, 40, 75), pill_rect, border_radius=24)
        _txt(surf, f"Nº de jogadores: {self.n_players}", L['F_MED'], C.WHITE, pill_rect.left + int(20*sc), pill_rect.centery - 2, "ml")
        
        pygame.draw.rect(surf, (0,0,0,20), rect_plus.move(2,2), border_radius=10)
        pygame.draw.rect(surf, (40, 180, 80), rect_plus, border_radius=10)
        _txt(surf, "+", L['F_MED'], C.WHITE, rect_plus.centerx, rect_plus.centery - 2)
        
        pygame.draw.rect(surf, (0,0,0,20), rect_minus.move(2,2), border_radius=10)
        pygame.draw.rect(surf, (180, 50, 80), rect_minus, border_radius=10)
        _txt(surf, "-", L['F_MED'], C.WHITE, rect_minus.centerx, rect_minus.centery - 4)
        
        # ── DESENHO DOS CARDS ──
        for i, (crect, type_rect, pick_rect) in enumerate(cards):
            act = i < self.n_players
            head_h = int(crect.height * 0.40)

            if not act:
                pygame.draw.rect(surf, (0,0,0,30), crect.move(5,5), border_radius=16)
                pygame.draw.rect(surf, (54, 42, 70), crect, border_radius=16)
                pygame.draw.rect(surf, (45, 35, 60), (crect.x, crect.y, crect.w, head_h), border_top_left_radius=16, border_top_right_radius=16)
                pygame.draw.line(surf, (40, 30, 55), (crect.x, crect.y + head_h), (crect.right - 1, crect.y + head_h), 2)
                pygame.draw.rect(surf, C.BLACK, crect, 2, border_radius=16)

                _txt(surf, f"Jogador {i+1}", L['F_SM'], (110, 100, 130), crect.centerx, crect.y + head_h//2 - 2)
                _txt(surf, "Desativado", L['F_MED'], (90, 80, 110), crect.centerx, crect.centery + int(15*sc) - 2)
                continue

            pygame.draw.rect(surf, (0,0,0,30), crect.move(5,5), border_radius=16)
            pygame.draw.rect(surf, (70, 56, 85), crect, border_radius=16)
            pygame.draw.rect(surf, C.PC[i], (crect.x, crect.y, crect.w, head_h), border_top_left_radius=16, border_top_right_radius=16)
            pygame.draw.line(surf, _sh(C.PC[i], 40), (crect.x, crect.y + head_h), (crect.right - 1, crect.y + head_h), 2)
            pygame.draw.rect(surf, C.BLACK, crect, 2, border_radius=16)

            avatar_sz = int(crect.height * 0.48)
            avatar_x = crect.x + int(15*sc) + avatar_sz//2
            avatar_y = crect.y + head_h - int(avatar_sz * 0.15)
            
            pygame.draw.circle(surf, _sh(C.PC[i], 30), (avatar_x, avatar_y+2), avatar_sz//2 + 2)
            pygame.draw.circle(surf, C.PC[i], (avatar_x, avatar_y), avatar_sz//2 + 2)
            
            img = _get_char_img(self.choices[i], avatar_sz)
            surf.blit(img, img.get_rect(center=(avatar_x, avatar_y)))

            text_x = avatar_x + avatar_sz//2 + int(12 * sc)
            name = C.CHARACTER_NAMES.get(self.choices[i], "Aleatório")

            # Alinhamento dos nomes ajustado (-2 na altura)
            _txt(surf, name, L['F_SM'], C.WHITE, text_x, crect.y + head_h // 2 - 2, "ml")
            _txt(surf, f"JOGADOR {i+1}", L['F_XXSM'], (210, 200, 220), text_x, crect.y + head_h + int(14 * sc), "ml")

            # Botões Modulares
            t_col = (40, 180, 80) if self.types[i] == "human" else (220, 60, 80)
            pygame.draw.rect(surf, (0,0,0,20), type_rect.move(2,2), border_radius=8)
            pygame.draw.rect(surf, t_col, type_rect, border_radius=8)
            pygame.draw.rect(surf, C.BLACK, type_rect, 1, border_radius=8)
            _txt(surf, "Humano" if self.types[i] == "human" else "CPU", L['F_XSM'], C.WHITE, type_rect.centerx, type_rect.centery - 2)

            pygame.draw.rect(surf, (0,0,0,20), pick_rect.move(2,2), border_radius=8)
            pygame.draw.rect(surf, (100, 85, 115), pick_rect, border_radius=8)
            pygame.draw.rect(surf, C.BLACK, pick_rect, 1, border_radius=8)
            _txt(surf, "Escolher", L['F_XSM'], C.WHITE, pick_rect.centerx, pick_rect.centery - 2)

        # Botão INICIAR
        pygame.draw.rect(surf, (0,0,0,20), start_rect.move(3,3), border_radius=20)
        pygame.draw.rect(surf, (40, 200, 90), start_rect, border_radius=20)
        _txt(surf, "INICIAR", L['F_MED'], C.WHITE, start_rect.centerx, start_rect.centery - 2)
        _txt(surf, "Setas = jogadores · ENTER = iniciar", L['F_XXSM'], (130, 120, 160), cx, start_rect.bottom + int(15*sc))

    # ── TELA PICKER (MODAL) ───────────────────────────────────────────────────
    def _draw_picker(self, surf, L):
        import os
        W, H, cx, sc = L['W'], L['H'], L['cx'], L['sc']
        i = self.picker_slot

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((15, 10, 30, 210)) 
        surf.blit(overlay, (0, 0))

        modal_w = min(W - 40, int(850 * sc))
        modal_h = min(H - 40, int(600 * sc))
        md_x = (W - modal_w) // 2
        md_y = (H - modal_h) // 2

        pygame.draw.rect(surf, (0,0,0,40), (md_x+5, md_y+5, modal_w, modal_h), border_radius=24)
        pygame.draw.rect(surf, (48, 42, 75), (md_x, md_y, modal_w, modal_h), border_radius=24)

        hdr_h = int(65 * sc)
        pygame.draw.rect(surf, (36, 30, 60), (md_x, md_y, modal_w, hdr_h), border_top_left_radius=24, border_top_right_radius=24)
        _txt(surf, f"Jogador {i+1} — Escolha seu personagem", L['F_MED'], C.WHITE, md_x + modal_w//2, md_y + hdr_h//2 - 2)

        back_w = int(40 * sc)
        back_h = int(40 * sc)
        back_x = md_x + int(15 * sc)
        back_y = md_y + (hdr_h - back_h) // 2

        try:
            voltar_img = pygame.image.load(os.path.join("images", "voltar.png")).convert_alpha()
            voltar_img = pygame.transform.smoothscale(voltar_img, (back_w, back_h))
            surf.blit(voltar_img, (back_x, back_y))
        except Exception:
            pygame.draw.rect(surf, (0,0,0,20), (back_x+2, back_y+2, back_w, back_h), border_radius=12)
            pygame.draw.rect(surf, (70, 56, 85), (back_x, back_y, back_w, back_h), border_radius=12)
            _txt(surf, "<-", L['F_BIG'], C.WHITE, back_x + back_w//2, back_y + back_h//2 - 4)

        cols = 6
        gap  = int(12 * sc)
        pad_x = int(20 * sc)
        pad_y = int(20 * sc)
        
        avail_w = modal_w - (pad_x * 2) - int(25 * sc)
        card_w  = (avail_w - (cols - 1) * gap) // cols
        card_h  = int(card_w * 1.15) 
        
        grid_x = md_x + pad_x
        grid_y = md_y + hdr_h + pad_y

        items = [None] + [slug for slug, _ in C.CHARACTER_ROSTER]
        rows_visible = max(1, (modal_h - hdr_h - pad_y * 2) // (card_h + gap))
        max_scroll   = max(0, (len(items) + cols - 1) // cols - rows_visible)
        self.picker_scroll = max(0, min(self.picker_scroll, max_scroll))

        if max_scroll > 0:
            sb_w = int(8 * sc)
            sb_h = modal_h - hdr_h - pad_y * 2
            sb_x = md_x + modal_w - pad_x - sb_w
            sb_y = grid_y
            
            pygame.draw.rect(surf, (36, 30, 60), (sb_x, sb_y, sb_w, sb_h), border_radius=4)
            thumb_h = max(int(20*sc), int(sb_h * (rows_visible / ((len(items) + cols - 1) // cols))))
            thumb_y = sb_y + (self.picker_scroll / max_scroll) * (sb_h - thumb_h)
            pygame.draw.rect(surf, C.PC[i], (sb_x, thumb_y, sb_w, thumb_h), border_radius=4)

        img_sz = int(card_h * 0.65)
        for idx, slug in enumerate(items):
            col_idx = idx % cols
            row_idx = idx // cols - self.picker_scroll
            
            if row_idx < 0 or row_idx >= rows_visible: continue

            rx = grid_x + col_idx * (card_w + gap)
            ry = grid_y + row_idx * (card_h + gap)
            cx_ = rx + card_w // 2

            selected = (slug == self.choices[i])
            hover    = (self._hover == idx)

            bg_col = C.PC[i] if selected else ((65, 55, 95) if hover else (54, 42, 70))
            
            pygame.draw.rect(surf, (0,0,0,20), (rx+3, ry+3, card_w, card_h), border_radius=12)
            pygame.draw.rect(surf, bg_col, (rx, ry, card_w, card_h), border_radius=12)
            if selected:
                pygame.draw.rect(surf, C.WHITE, (rx, ry, card_w, card_h), 2, border_radius=12)

            sh_surf = _get_char_shadow(slug, img_sz)
            sh_rect = sh_surf.get_rect(center=(cx_, ry + int(card_h*0.4) + 4))
            surf.blit(sh_surf, sh_rect)
            
            img = _get_char_img(slug, img_sz)
            surf.blit(img, img.get_rect(center=(cx_, ry + int(card_h*0.4))))
            
            name = C.CHARACTER_NAMES.get(slug, "Aleatório")
            _txt(surf, name, L['F_XXSM'], C.WHITE, cx_, ry + int(card_h*0.82) - 2)

        self._picker_meta = dict(
            items=items, cols=cols, card_w=card_w, card_h=card_h, gap=gap,
            grid_x=grid_x, grid_y=grid_y, rows_visible=rows_visible,
            back=(back_x, back_y, back_w, back_h),
        )

    # ── Eventos ───────────────────────────────────────────────────────────────
    def handle(self, event):
        if self.screen == "picker": return self._handle_picker(event)
        return self._handle_main(event)

    def _handle_main(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:   self.n_players = min(4, self.n_players + 1)
            if event.key == pygame.K_DOWN: self.n_players = max(2, self.n_players - 1)
            if event.key == pygame.K_RETURN: return "start"

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            pill_rect, rect_plus, rect_minus, cards, start_rect = self._layout(self._L())

            if rect_plus.collidepoint(mx, my):  self.n_players = min(4, self.n_players + 1)
            if rect_minus.collidepoint(mx, my): self.n_players = max(2, self.n_players - 1)

            for i, (crect, type_rect, pick_rect) in enumerate(cards):
                if i >= self.n_players: continue
                if i > 0 and type_rect.collidepoint(mx, my):
                    self.types[i] = "cpu" if self.types[i] == "human" else "human"
                if pick_rect.collidepoint(mx, my):
                    self.picker_slot, self.picker_scroll, self.screen, self._hover = i, 0, "picker", None

            if start_rect.collidepoint(mx, my):
                return "start"
        return None

    def _handle_picker(self, event):
        m = getattr(self, '_picker_meta', None)
        if not m: return None

        if event.type == pygame.MOUSEMOTION:
            self._hover = self._picker_hit(event.pos, m)

        if event.type == pygame.MOUSEWHEEL:
            self.picker_scroll = max(0, self.picker_scroll - event.y)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: self.screen = "main"
            if event.key in (pygame.K_UP, pygame.K_PAGEUP): self.picker_scroll = max(0, self.picker_scroll - 1)
            if event.key in (pygame.K_DOWN, pygame.K_PAGEDOWN): self.picker_scroll += 1
            if event.key == pygame.K_RETURN: self.screen = "main"

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in (4, 5): return 
            
            mx, my = event.pos
            bx, by, bw, bh = m['back']
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self.screen = "main"
                return None

            hit = self._picker_hit(event.pos, m)
            if hit is not None:
                self.choices[self.picker_slot] = m['items'][hit]
                self.screen = "main" 
        return None

    def _picker_hit(self, pos, m):
        mx, my = pos
        for idx in range(len(m['items'])):
            c, r = idx % m['cols'], idx // m['cols'] - self.picker_scroll
            if r < 0 or r >= m['rows_visible']: continue
            rx = m['grid_x'] + c * (m['card_w'] + m['gap'])
            ry = m['grid_y'] + r * (m['card_h'] + m['gap'])
            if rx <= mx <= rx + m['card_w'] and ry <= my <= ry + m['card_h']:
                return idx
        return None
    
    # ── Construir Game ────────────────────────────────────────────────────────
    def make_game(self):
        from game import Game
        
        used_slugs = set(s for s in self.choices[:self.n_players] if s is not None)
        available  = [slug for slug, _ in C.CHARACTER_ROSTER if slug not in used_slugs]
        random.shuffle(available)

        for i in range(self.n_players):
            if self.choices[i] is None:
                self.choices[i] = available.pop(0) if available else C.CHARACTER_ROSTER[i % len(C.CHARACTER_ROSTER)][0]

        C.PLAYER_CHOICES.clear()
        C.PLAYER_DISPLAY_NAMES.clear()
        for i in range(self.n_players):
            slug = self.choices[i]
            C.PLAYER_CHOICES[i] = slug
            C.PLAYER_DISPLAY_NAMES[i] = C.CHARACTER_NAMES.get(slug, slug.capitalize())

        players = [Player(0, True)] + [Player(i, self.types[i] == "human") for i in range(1, self.n_players)]
        
        return Game(players)