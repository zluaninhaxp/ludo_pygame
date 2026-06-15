"""
menu.py — Tela de configuração da partida com seleção de personagens.
Sem emojis para evitar quadrados (tofu) nas fontes do sistema.
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

def _txt(surf, text, font, color, cx, cy, anchor="c"):
    img = font.render(str(text), True, color)
    r   = img.get_rect()
    if anchor == "c":    r.center   = (cx, cy)
    elif anchor == "tl": r.topleft  = (cx, cy)
    elif anchor == "tc": r.midtop   = (cx, cy)
    elif anchor == "tr": r.topright = (cx, cy)
    surf.blit(img, r)

# ── Cache de imagens de personagens ──────────────────────────────────────────
_CHAR_IMG_CACHE = {}

def _get_char_img(slug, size):
    """
    Retorna a imagem do personagem.
    Se slug for None, carrega a imagem 'random.png' para Aleatório.
    """
    key = (slug, size)
    if key in _CHAR_IMG_CACHE:
        return _CHAR_IMG_CACHE[key]
        
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    import os

    # Se for Aleatório (None), procura o arquivo random.png. Senão, procura o nome normal.
    arquivo = "random" if slug is None else slug
    path = os.path.join("images", f"{arquivo}.png")
    
    try:
        img = pygame.image.load(path).convert_alpha()
        ow, oh = img.get_size()
        scale  = min(size / ow, size / oh)
        
        # --- ADICIONE ESTAS DUAS LINHAS AQUI ---
        if slug is None:
            scale *= 0.7  # Diminui a imagem do random para 70% do tamanho
        # --------------------------------------

        nw, nh = int(ow * scale), int(oh * scale)
        img    = pygame.transform.smoothscale(img, (nw, nh))
        surf.blit(img, ((size - nw) // 2, (size - nh) // 2))
    except Exception:
        # Fallback de segurança se a imagem não existir na pasta
        pygame.draw.circle(surf, (80, 70, 110), (size//2, size//2), size//2 - 2)
        pygame.draw.circle(surf, (150, 140, 180), (size//2, size//2), size//2 - 2, 2)
        font = _load_font(int(size * 0.5), bold=True)
        # Bota '?' se era pra ser o random, ou 'X' se era pra ser um personagem faltante
        texto_fallback = "?" if slug is None else "X"
        _txt(surf, texto_fallback, font, (255, 255, 255), size//2, size//2)

    _CHAR_IMG_CACHE[key] = surf
    return surf

# ── Constantes visuais ────────────────────────────────────────────────────────
_INK      = (52,  42,  76)
_BG       = C.BG
_PANEL    = (36,  26,  64)
_EDGE     = (72,  58, 112)
_CARD_ACT = (62,  52,  98)
_CARD_OFF = (32,  24,  52)
_GOLD     = (255, 220,  30)
_DIM      = (110, 100, 140)
_WHITE    = C.WHITE

class Menu:
    def __init__(self):
        self.n_players   = 2
        self.types       = ["human", "cpu", "cpu", "cpu"]
        self.choices     = [None, None, None, None]
        self.screen      = "main"
        self.picker_slot = 0
        self.picker_scroll = 0
        self._hover      = None

    def _L(self):
        W = C.W; H = C.H; cx = W // 2
        sc = min(W / 960, H / 720)
        return dict(
            W=W, H=H, cx=cx, sc=sc,
            F_BIG  = _load_font(max(16, int(40 * sc)), bold=True),
            F_MED  = _load_font(max(13, int(24 * sc)), bold=True),
            F_SM   = _load_font(max(11, int(18 * sc)), bold=True),
            F_XSM  = _load_font(max(9,  int(14 * sc))),
        )

    # ── TELA PRINCIPAL ────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface):
        if self.screen == "picker":
            self._draw_picker(surf)
        else:
            self._draw_main(surf)

    def _draw_main(self, surf: pygame.Surface):
        L  = self._L()
        W  = L['W']; H = L['H']; cx = L['cx']; sc = L['sc']
        F_BIG = L['F_BIG']; F_MED = L['F_MED']
        F_SM  = L['F_SM'];  F_XSM = L['F_XSM']

        surf.fill(_BG)

        title_y = max(38, int(H * 0.07))
        _txt(surf, "LUDO", F_BIG, _GOLD, cx, title_y)
        _txt(surf, "Configuracao da Partida", F_SM, _DIM, cx, title_y + int(40 * sc))

        # ── Número de jogadores (Usando + e -) ───────────────────────────────
        ny     = title_y + int(90 * sc)
        btn_sz = max(22, int(30 * sc))
        lbl_x  = cx - int(110 * sc)
        num_x  = cx + int(40 * sc)
        bx_up  = cx + int(80 * sc)
        bx_dn  = cx + int(116 * sc)

        _txt(surf, "Nº de jogadores:", F_SM, _WHITE, lbl_x, ny, anchor="c")
        _txt(surf, str(self.n_players), F_BIG, _GOLD, num_x, ny)

        for label, bx, col in [("+", bx_up, (50,160,60)), ("-", bx_dn, (180,50,50))]:
            pygame.draw.rect(surf, col,
                             (bx - btn_sz//2, ny - btn_sz//2, btn_sz, btn_sz),
                             border_radius=6)
            _txt(surf, label, F_SM, _WHITE, bx, ny - 2)

        # ── Cards dos slots ───────────────────────────────────────────────────
        card_y0  = ny + int(50 * sc)
        card_gap = max(70, int(H * 0.115))
        card_w   = max(320, int(W * 0.40))
        card_h   = max(62, int(H * 0.095))
        card_x   = cx - card_w // 2
        img_sz   = int(card_h * 0.78)

        for i in range(4):
            y   = card_y0 + i * card_gap
            act = i < self.n_players

            bg_col = _CARD_ACT if act else _CARD_OFF
            pygame.draw.rect(surf, bg_col, (card_x, y, card_w, card_h), border_radius=12)
            if act:
                pygame.draw.rect(surf, C.PC[i], (card_x, y, card_w, card_h), 3, border_radius=12)
            else:
                pygame.draw.rect(surf, _EDGE,   (card_x, y, card_w, card_h), 1, border_radius=12)

            if not act:
                _txt(surf, f"Jogador {i+1} — desativado", F_XSM, _DIM, cx, y + card_h//2)
                continue

            # Avatar (Se slug for None, desenha o "?")
            slug = self.choices[i]
            img  = _get_char_img(slug, img_sz)
            
            img_x = card_x + int(card_h * 0.1)
            img_y = y + (card_h - img_sz) // 2
            surf.blit(img, (img_x, img_y))

            # Nome do personagem
            char_name = C.CHARACTER_NAMES.get(slug, slug) if slug else "Aleatorio"
            text_x    = img_x + img_sz + max(10, int(12 * sc))
            _txt(surf, f"Jogador {i+1}", F_XSM, C.PL[i], text_x, y + int(card_h * 0.28), anchor="tl")
            _txt(surf, char_name, F_SM, _WHITE, text_x, y + int(card_h * 0.54), anchor="tl")

            # Tipo (humano/cpu)
            t      = self.types[i]
            type_w = max(74, int(card_w * 0.22))
            type_h = max(28, int(card_h * 0.44))
            type_x = card_x + card_w - type_w - max(8, int(10 * sc))
            type_y = y + int(card_h * 0.15)
            t_col  = (40, 150, 50) if t == "human" else (150, 45, 45)
            pygame.draw.rect(surf, t_col, (type_x, type_y, type_w, type_h), border_radius=8)
            _txt(surf, "Humano" if t == "human" else "CPU", F_XSM, _WHITE,
                 type_x + type_w//2, type_y + type_h//2)

            # Botão "Escolher personagem"
            pick_w = max(130, int(card_w * 0.38))
            pick_h = max(24, int(card_h * 0.38))
            pick_x = card_x + card_w - pick_w - max(8, int(10 * sc))
            pick_y = type_y + type_h + max(4, int(5 * sc))
            pygame.draw.rect(surf, (55, 45, 90), (pick_x, pick_y, pick_w, pick_h), border_radius=7)
            pygame.draw.rect(surf, _EDGE, (pick_x, pick_y, pick_w, pick_h), 1, border_radius=7)
            _txt(surf, "Escolher", F_XSM, (180, 170, 220),
                 pick_x + pick_w//2, pick_y + pick_h//2)

        note_y = card_y0 - int(18 * sc)
        _txt(surf, "Jogador 1 sempre Humano", F_XSM, _DIM, cx, note_y)

        # Botão INICIAR
        btn_w = max(180, int(W * 0.21))
        btn_h = max(44,  int(H * 0.075))
        btn_x = cx - btn_w // 2
        btn_y = H - max(70, int(H * 0.12))
        pygame.draw.rect(surf, (38, 140, 50), (btn_x, btn_y, btn_w, btn_h), border_radius=14)
        pygame.draw.rect(surf, (80, 200, 90), (btn_x, btn_y, btn_w, btn_h), 2, border_radius=14)
        _txt(surf, "INICIAR", F_MED, _WHITE, cx, btn_y + btn_h//2)

        _txt(surf, "Setas = jogadores  |  ENTER = iniciar",
             F_XSM, _DIM, cx, H - max(22, int(H * 0.04)))

    # ── TELA PICKER ───────────────────────────────────────────────────────────
    def _draw_picker(self, surf: pygame.Surface):
        L  = self._L()
        W  = L['W']; H = L['H']; cx = L['cx']; sc = L['sc']
        F_BIG = L['F_BIG']; F_MED = L['F_MED']
        F_SM  = L['F_SM'];  F_XSM = L['F_XSM']
        i = self.picker_slot

        surf.fill(_BG)

        hdr_h = max(54, int(H * 0.09))
        pygame.draw.rect(surf, _PANEL, (0, 0, W, hdr_h))
        pygame.draw.rect(surf, C.PC[i], (0, 0, W, hdr_h), 3)
        _txt(surf, f"Jogador {i+1} — Escolha seu personagem", F_MED, _WHITE, cx, hdr_h//2)

        # Botão voltar (usando <)
        back_w = max(80, int(W * 0.09))
        back_h = max(30, int(hdr_h * 0.58))
        back_x = max(10, int(W * 0.012))
        back_y = (hdr_h - back_h) // 2
        pygame.draw.rect(surf, (70, 55, 110), (back_x, back_y, back_w, back_h), border_radius=8)
        pygame.draw.rect(surf, _EDGE, (back_x, back_y, back_w, back_h), 1, border_radius=8)
        _txt(surf, "< Voltar", F_XSM, _WHITE, back_x + back_w//2, back_y + back_h//2)

        cols   = max(3, min(6, int(W / max(120, int(130 * sc)))))
        card_w = (W - max(24, int(W * 0.03)) * 2) // cols
        card_h = max(110, int(card_w * 1.2))
        img_sz = max(60, int(card_h * 0.62))
        pad_x  = (W - cols * card_w) // 2
        grid_y = hdr_h + max(10, int(H * 0.015))

        items = [None] + [slug for slug, _ in C.CHARACTER_ROSTER]
        current = self.choices[i]

        rows_visible = max(1, (H - grid_y - max(50, int(H * 0.08))) // card_h)
        max_scroll   = max(0, (len(items) + cols - 1) // cols - rows_visible)
        self.picker_scroll = max(0, min(self.picker_scroll, max_scroll))

        for idx, slug in enumerate(items):
            col_idx = idx % cols
            row_idx = idx // cols - self.picker_scroll
            if row_idx < 0 or row_idx >= rows_visible:
                continue

            cx_ = pad_x + col_idx * card_w + card_w // 2
            cy_ = grid_y + row_idx * card_h

            selected = (slug == current)
            hover    = (self._hover == idx)

            bg = C.PC[i] if selected else ((72, 58, 106) if hover else (44, 34, 72))
            border = _GOLD if selected else (C.PL[i] if hover else _EDGE)

            pygame.draw.rect(surf, bg,
                             (pad_x + col_idx * card_w + 4, cy_ + 4, card_w - 8, card_h - 8),
                             border_radius=12)
            pygame.draw.rect(surf, border,
                             (pad_x + col_idx * card_w + 4, cy_ + 4, card_w - 8, card_h - 8),
                             2 if not selected else 3, border_radius=12)

            img = _get_char_img(slug, img_sz)
            surf.blit(img, (cx_ - img_sz//2, cy_ + int(card_h * 0.06)))
            
            name = C.CHARACTER_NAMES.get(slug, slug) if slug else "Aleatorio"
            _txt(surf, name, F_XSM, _GOLD if selected else _WHITE, cx_, cy_ + int(card_h * 0.78))

            if selected:
                _txt(surf, "OK", F_SM, _GOLD, cx_ + card_w//2 - 16, cy_ + 8, anchor="c")

        if self.picker_scroll > 0:
            _txt(surf, "+ acima", F_XSM, _DIM, cx, grid_y + 8)
        if self.picker_scroll < max_scroll:
            _txt(surf, "+ abaixo", F_XSM, _DIM, cx, H - max(28, int(H * 0.045)))

        conf_w = max(160, int(W * 0.19))
        conf_h = max(40,  int(H * 0.068))
        conf_x = cx - conf_w // 2
        conf_y = H - max(60, int(H * 0.1))
        pygame.draw.rect(surf, (38, 140, 50), (conf_x, conf_y, conf_w, conf_h), border_radius=12)
        pygame.draw.rect(surf, (80, 200, 90), (conf_x, conf_y, conf_w, conf_h), 2, border_radius=12)
        _txt(surf, "Confirmar", F_MED, _WHITE, cx, conf_y + conf_h//2)

        self._picker_meta = dict(
            items=items, cols=cols, card_w=card_w, card_h=card_h,
            pad_x=pad_x, grid_y=grid_y, rows_visible=rows_visible,
            back=(back_x, back_y, back_w, back_h),
            conf=(conf_x, conf_y, conf_w, conf_h),
            hdr_h=hdr_h,
        )

    # ── Eventos ───────────────────────────────────────────────────────────────
    def handle(self, event) -> "str | None":
        if self.screen == "picker":
            return self._handle_picker(event)
        return self._handle_main(event)

    def _handle_main(self, event) -> "str | None":
        L  = self._L()
        W  = L['W']; H = L['H']; cx = L['cx']; sc = L['sc']

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.n_players = min(4, self.n_players + 1)
            elif event.key == pygame.K_DOWN:
                self.n_players = max(2, self.n_players - 1)
            elif event.key == pygame.K_RETURN:
                return "start"

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            ny     = max(38, int(H * 0.07)) + int(90 * sc)
            btn_sz = max(22, int(30 * sc))
            bx_up  = cx + int(80 * sc)
            bx_dn  = cx + int(116 * sc)
            if abs(mx - bx_up) < btn_sz//2 and abs(my - ny) < btn_sz//2:
                self.n_players = min(4, self.n_players + 1)
            if abs(mx - bx_dn) < btn_sz//2 and abs(my - ny) < btn_sz//2:
                self.n_players = max(2, self.n_players - 1)

            card_y0  = ny + int(50 * sc)
            card_gap = max(70, int(H * 0.115))
            card_w   = max(320, int(W * 0.40))
            card_h   = max(62, int(H * 0.095))
            card_x   = cx - card_w // 2

            for i in range(self.n_players):
                y = card_y0 + i * card_gap
                if not (card_x <= mx <= card_x + card_w and y <= my <= y + card_h):
                    continue

                if i > 0:
                    type_w = max(74, int(card_w * 0.22))
                    type_h = max(28, int(card_h * 0.44))
                    type_x = card_x + card_w - type_w - max(8, int(10 * sc))
                    type_y = y + int(card_h * 0.15)
                    if type_x <= mx <= type_x + type_w and type_y <= my <= type_y + type_h:
                        self.types[i] = "cpu" if self.types[i] == "human" else "human"
                        return None

                type_h = max(28, int(card_h * 0.44))
                type_y = y + int(card_h * 0.15)
                type_w = max(74, int(card_w * 0.22))
                type_x = card_x + card_w - type_w - max(8, int(10 * sc))
                pick_w = max(130, int(card_w * 0.38))
                pick_h = max(24, int(card_h * 0.38))
                pick_x = card_x + card_w - pick_w - max(8, int(10 * sc))
                pick_y = type_y + type_h + max(4, int(5 * sc))
                if pick_x <= mx <= pick_x + pick_w and pick_y <= my <= pick_y + pick_h:
                    self.picker_slot   = i
                    self.picker_scroll = 0
                    self.screen        = "picker"
                    self._hover        = None
                    return None

            btn_w = max(180, int(W * 0.21))
            btn_h = max(44,  int(H * 0.075))
            btn_x = cx - btn_w // 2
            btn_y = H - max(70, int(H * 0.12))
            if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h:
                return "start"

        return None

    def _handle_picker(self, event) -> "str | None":
        if not hasattr(self, '_picker_meta'):
            return None
        m = self._picker_meta
        items        = m['items']
        cols         = m['cols']
        card_w       = m['card_w']
        card_h       = m['card_h']
        pad_x        = m['pad_x']
        grid_y       = m['grid_y']
        rows_visible = m['rows_visible']
        bx, by, bw, bh = m['back']
        cx_, cy_, cw, ch = m['conf']

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._hover = self._picker_hit(mx, my, items, cols, card_w, card_h, pad_x, grid_y, rows_visible)

        if event.type == pygame.MOUSEWHEEL:
            self.picker_scroll = max(0, self.picker_scroll - event.y)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.screen = "main"
            elif event.key in (pygame.K_UP, pygame.K_PAGEUP):
                self.picker_scroll = max(0, self.picker_scroll - 1)
            elif event.key in (pygame.K_DOWN, pygame.K_PAGEDOWN):
                self.picker_scroll += 1
            elif event.key == pygame.K_RETURN:
                self.screen = "main"

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self.screen = "main"
                return None

            if cx_ <= mx <= cx_ + cw and cy_ <= my <= cy_ + ch:
                self.screen = "main"
                return None

            hit = self._picker_hit(mx, my, items, cols, card_w, card_h, pad_x, grid_y, rows_visible)
            if hit is not None:
                self.choices[self.picker_slot] = items[hit]

        return None

    def _picker_hit(self, mx, my, items, cols, card_w, card_h, pad_x, grid_y, rows_visible):
        for idx in range(len(items)):
            col_idx = idx % cols
            row_idx = idx // cols - self.picker_scroll
            if row_idx < 0 or row_idx >= rows_visible:
                continue
            rx = pad_x + col_idx * card_w + 4
            ry = grid_y + row_idx * card_h + 4
            rw = card_w - 8
            rh = card_h - 8
            if rx <= mx <= rx + rw and ry <= my <= ry + rh:
                return idx
        return None

    # ── Construir Game ────────────────────────────────────────────────────────
    def make_game(self):
        from game import Game

        used_slugs = set(s for s in self.choices[:self.n_players] if s is not None)
        available  = [slug for slug, _ in C.CHARACTER_ROSTER if slug not in used_slugs]
        random.shuffle(available)

        final_choices = {}
        for i in range(self.n_players):
            slug = self.choices[i]
            if slug is None:
                if available:
                    slug = available.pop(0)
                else:
                    slug = C.CHARACTER_ROSTER[i % len(C.CHARACTER_ROSTER)][0]
            final_choices[i] = slug

        C.PLAYER_CHOICES.clear()
        C.PLAYER_DISPLAY_NAMES.clear()
        for i in range(self.n_players):
            slug = final_choices[i]
            C.PLAYER_CHOICES[i]       = slug
            C.PLAYER_DISPLAY_NAMES[i] = C.CHARACTER_NAMES.get(slug, slug.capitalize())

        players = [Player(0, True)]
        for i in range(1, self.n_players):
            players.append(Player(i, self.types[i] == "human"))
        return Game(players)