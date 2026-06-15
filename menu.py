"""
menu.py — Tela de configuração da partida com seleção de personagens.

Fluxo de telas:
  1. "setup"   — escolhe nº de jogadores e tipo (humano/CPU)
  2. "pick_N"  — galeria de personagens para o jogador N escolher
  3. (jogo começa)

Regras:
  · Mínimo 2, máximo 4 jogadores
  · Pelo menos 1 humano (Jogador 1 sempre humano)
  · Cada jogador pode escolher um personagem específico ou "Aleatório"
  · Personagens já escolhidos ficam marcados mas ainda selecionáveis
    (permite que dois jogadores usem o mesmo rosto, se quiserem)
"""

import pygame
import os
import random
import constants as C
from constants import (
    W, H, BG, PC, PL, PD, PN,
    DGRAY, WHITE, LGRAY,
    CHARACTER_CATALOG, PLAYER_CHOICES,
)
from piece import Player

pygame.font.init()

# ── Fontes ────────────────────────────────────────────────────────────────────
def _lf(size, bold=False):
    for name in ("Fredoka One", "Nunito", "Varela Round",
                 "Comic Sans MS", "Arial Rounded MT Bold", "Arial"):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.SysFont(None, size, bold=bold)

F_TITLE = _lf(42, bold=True)
F_BIG   = _lf(32, bold=True)
F_MED   = _lf(22, bold=True)
F_SM    = _lf(17, bold=True)
F_XSM   = _lf(13)

# ── Paleta ────────────────────────────────────────────────────────────────────
_INK      = (52,  42,  76)
_PANEL    = (36,  26,  64)
_CARD_I   = (54,  42,  86)
_HINT     = (255, 222,  60)
_DIM      = (125, 112, 158)
_TAKEN    = (80,  68, 110)   # fundo de personagem já escolhido
_GREEN    = (45,  168,  45)
_GREEN_D  = (20,  110,  20)
_RED      = (168,  45,  45)

# ── Utilidades ────────────────────────────────────────────────────────────────
def _txt(surf, text, font, color, cx, cy, anchor="c"):
    img = font.render(str(text), True, color)
    r   = img.get_rect()
    if   anchor == "c":  r.center   = (cx, cy)
    elif anchor == "tl": r.topleft  = (cx, cy)
    elif anchor == "tc": r.midtop   = (cx, cy)
    elif anchor == "tr": r.topright = (cx, cy)
    surf.blit(img, r)

def _sh(c, a=40):
    return (max(c[0]-a,0), max(c[1]-a,0), max(c[2]-a,0))

def _btn(surf, label, font, rx, ry, rw, rh, bg, border, text_col=WHITE, radius=10):
    """Desenha um botão flat com sombra e retorna o Rect."""
    rect = pygame.Rect(rx, ry, rw, rh)
    sh   = rect.move(0, 3)
    pygame.draw.rect(surf, _sh(bg, 50), sh,   border_radius=radius)
    pygame.draw.rect(surf, bg,          rect, border_radius=radius)
    pygame.draw.rect(surf, border,      rect, 2, border_radius=radius)
    pygame.draw.rect(surf, _INK,        rect, 1, border_radius=radius)
    _txt(surf, label, font, text_col, rect.centerx, rect.centery)
    return rect

# ── Cache de imagens ──────────────────────────────────────────────────────────
_IMG_CACHE: dict = {}

def _load_char_img(key: str, size: int) -> pygame.Surface:
    cache_key = (key, size)
    if cache_key in _IMG_CACHE:
        return _IMG_CACHE[cache_key]

    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    path = os.path.join("images", f"{key}.png")
    try:
        img  = pygame.image.load(path).convert_alpha()
        w, h = img.get_size()
        sc   = min(size / w, size / h)
        img  = pygame.transform.smoothscale(img, (int(w*sc), int(h*sc)))
        ox   = (size - img.get_width())  // 2
        oy   = (size - img.get_height()) // 2
        surf.blit(img, (ox, oy))
    except Exception:
        # Placeholder colorido se a imagem não existir
        pygame.draw.rect(surf, (80, 70, 100), (0, 0, size, size), border_radius=size//4)
        _txt(surf, key[:2].upper(), F_SM, WHITE, size//2, size//2)

    _IMG_CACHE[cache_key] = surf
    return surf


# ══════════════════════════════════════════════════════════════════════════════
class Menu:
    def __init__(self):
        self.n_players = 2
        # "human" ou "cpu" para cada slot 0-3
        self.types     = ["human", "cpu", "cpu", "cpu"]
        # Chave do personagem escolhido (None = aleatório)
        self.choices   = [None, None, None, None]

        # Tela atual: "setup" | "pick" (galeria)
        self.screen    = "setup"
        self.pick_slot = 0          # qual jogador está escolhendo
        self.scroll_y  = 0          # scroll da galeria
        self._gallery_rects = []    # [(char_idx, Rect)] para hit-test

    # ── API pública ───────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface):
        surf.fill(BG)
        if self.screen == "setup":
            self._draw_setup(surf)
        else:
            self._draw_gallery(surf)

    def handle(self, event) -> str | None:
        """Retorna 'start' quando o jogo deve começar."""
        if self.screen == "setup":
            return self._handle_setup(event)
        else:
            return self._handle_gallery(event)

    def make_game(self):
        """Finaliza escolhas aleatórias e cria o Game."""
        from game import Game

        used = set(c for c in self.choices[:self.n_players] if c is not None)
        available = [ch["key"] for ch in CHARACTER_CATALOG]

        # Resolve aleatórios — preferindo não repetir, mas sem bloquear
        for i in range(self.n_players):
            if self.choices[i] is None:
                pool = [k for k in available if k not in used] or available
                chosen = random.choice(pool)
                self.choices[i] = chosen
                used.add(chosen)

        # Atualiza globals em constants para que renderer.py use os valores certos
        for i in range(self.n_players):
            C.PLAYER_CHOICES[i] = self.choices[i]
            # Atualiza o nome de exibição com o nome real do personagem
            char = next((ch for ch in CHARACTER_CATALOG
                         if ch["key"] == self.choices[i]), None)
            C.PN[i] = char["name"] if char else f"Jogador {i+1}"

        players = []
        for i in range(self.n_players):
            players.append(Player(i, self.types[i] == "human"))
        return Game(players)

    # ── Tela 1: Setup ─────────────────────────────────────────────────────────
    def _draw_setup(self, surf: pygame.Surface):
        cx = W // 2

        # Título
        _txt(surf, "🎲  L U D O", F_TITLE, _HINT, cx, 55)
        _txt(surf, "Configuração da Partida", F_SM, _DIM, cx, 102)

        # ── Nº de jogadores ──────────────────────────────────────────────────
        by = 148
        _txt(surf, "Número de jogadores:", F_SM, WHITE, cx - 80, by)

        # Botões – e +
        bw, bh = 36, 36
        self._btn_minus = _btn(surf, "–", F_BIG, cx + 46, by - bh//2,
                               bw, bh, _RED, _sh(_RED))
        self._btn_plus  = _btn(surf, "+", F_BIG, cx + 90, by - bh//2,
                               bw, bh, _GREEN, _sh(_GREEN))
        _txt(surf, str(self.n_players), F_BIG, _HINT, cx + 22, by)

        # ── Cards de jogadores ───────────────────────────────────────────────
        self._player_rows = {}   # slot → (toggle_rect, pick_rect)
        card_w, card_h = 560, 68
        card_x = cx - card_w // 2

        for i in range(4):
            y = 186 + i * 80

            active = (i < self.n_players)
            alpha_color = WHITE if active else (60, 55, 80)
            bg_color = (50, 40, 78) if active else (32, 26, 52)

            pygame.draw.rect(surf, bg_color,   (card_x, y, card_w, card_h), border_radius=12)
            if active:
                pygame.draw.rect(surf, PC[i], (card_x, y, card_w, card_h), 2, border_radius=12)
            pygame.draw.rect(surf, _INK,       (card_x, y, card_w, card_h), 1, border_radius=12)

            # Número do jogador
            circle_col = PC[i] if active else (60, 52, 85)
            pygame.draw.circle(surf, circle_col, (card_x + 30, y + card_h//2), 18)
            _txt(surf, str(i+1), F_MED, WHITE, card_x + 30, y + card_h//2)

            if not active:
                _txt(surf, f"Slot {i+1} — inativo", F_XSM, (70, 65, 95),
                     card_x + card_w//2, y + card_h//2)
                continue

            # Nome/preview do personagem escolhido
            char_key = self.choices[i]
            if char_key:
                char = next((c for c in CHARACTER_CATALOG if c["key"] == char_key), None)
                char_label = char["name"] if char else char_key
                # Miniatura
                thumb = _load_char_img(char_key, 46)
                surf.blit(thumb, (card_x + 56, y + card_h//2 - 23))
                _txt(surf, char_label, F_SM, alpha_color, card_x + 130, y + card_h//2)
            else:
                # Ícone "?" aleatório
                pygame.draw.circle(surf, (70, 60, 100), (card_x + 79, y + card_h//2), 23)
                _txt(surf, "?", F_BIG, _DIM, card_x + 79, y + card_h//2)
                _txt(surf, "Aleatório", F_SM, _DIM, card_x + 130, y + card_h//2)

            # Botão "Escolher"
            pick_rect = _btn(surf, "👤 Escolher", F_XSM,
                             card_x + card_w - 170, y + 14, 120, 34,
                             (70, 55, 110), (100, 80, 150))

            # Botão Humano/CPU (só slots 1-3; slot 0 sempre humano)
            if i == 0:
                _txt(surf, "Humano (fixo)", F_XSM, PL[0],
                     card_x + card_w - 46, y + card_h//2)
                toggle_rect = None
            else:
                t   = self.types[i]
                col = _GREEN if t == "human" else _RED
                toggle_rect = _btn(surf,
                                   "Humano" if t == "human" else "  CPU  ",
                                   F_XSM,
                                   card_x + card_w - 46 - 80, y + 14,
                                   80, 34, col, _sh(col))

            self._player_rows[i] = (toggle_rect, pick_rect)

        # ── Botão Iniciar ─────────────────────────────────────────────────────
        self._btn_start = _btn(surf, "▶   INICIAR", F_MED,
                               cx - 110, H - 88, 220, 52,
                               _GREEN, _GREEN_D, radius=14)

        _txt(surf, "Clique em 👤 Escolher para selecionar o personagem de cada jogador",
             F_XSM, _DIM, cx, H - 30)

    def _handle_setup(self, event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.n_players = min(4, self.n_players + 1)
            elif event.key == pygame.K_DOWN:
                self.n_players = max(2, self.n_players - 1)
            elif event.key == pygame.K_RETURN:
                return "start"

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if hasattr(self, "_btn_plus") and self._btn_plus.collidepoint(mx, my):
                self.n_players = min(4, self.n_players + 1)
                return None
            if hasattr(self, "_btn_minus") and self._btn_minus.collidepoint(mx, my):
                self.n_players = max(2, self.n_players - 1)
                return None
            if hasattr(self, "_btn_start") and self._btn_start.collidepoint(mx, my):
                return "start"

            for i, (toggle_rect, pick_rect) in self._player_rows.items():
                if i >= self.n_players:
                    continue
                if pick_rect and pick_rect.collidepoint(mx, my):
                    self.pick_slot = i
                    self.screen    = "pick"
                    self.scroll_y  = 0
                    return None
                if toggle_rect and toggle_rect.collidepoint(mx, my):
                    self.types[i] = "cpu" if self.types[i] == "human" else "human"
                    return None

        if event.type == pygame.MOUSEWHEEL:
            pass  # sem scroll no setup

        return None

    # ── Tela 2: Galeria de personagens ────────────────────────────────────────
    _COLS      = 5
    _THUMB     = 100   # tamanho da miniatura
    _GAP       = 16
    _GALL_TOP  = 110   # y onde começa a grelha
    _GALL_BOT  = H - 70

    def _draw_gallery(self, surf: pygame.Surface):
        slot  = self.pick_slot
        cx    = W // 2
        n     = len(CHARACTER_CATALOG)
        cols  = self._COLS
        th    = self._THUMB
        gap   = self._GAP

        total_w = cols * th + (cols - 1) * gap
        start_x = cx - total_w // 2

        # Cabeçalho
        slot_col = PC[slot]
        pygame.draw.rect(surf, (28, 20, 55), (0, 0, W, self._GALL_TOP - 4))
        _txt(surf, f"Jogador {slot+1} — escolha seu personagem",
             F_MED, slot_col, cx, 36)
        _txt(surf, "Clique para escolher  •  ESC ou ← para voltar  •  scroll para rolar",
             F_XSM, _DIM, cx, 68)

        # Botão "Aleatório" no topo
        self._btn_random = _btn(surf, "🎲  Aleatório (surpresa!)", F_SM,
                                cx - 140, 84, 280, 34,
                                (80, 60, 130), (110, 88, 170))

        # Linha separadora
        pygame.draw.line(surf, (60, 50, 90), (0, self._GALL_TOP - 4),
                         (W, self._GALL_TOP - 4), 2)

        # Área de scroll — clip para não vazar
        clip = pygame.Rect(0, self._GALL_TOP, W, self._GALL_BOT - self._GALL_TOP)
        surf.set_clip(clip)

        self._gallery_rects = []
        row_h = th + gap + 22   # thumb + gap + nome

        # Total de linhas e altura de conteúdo
        rows      = (n + cols - 1) // cols
        content_h = rows * row_h + gap
        max_scroll = max(0, content_h - (self._GALL_BOT - self._GALL_TOP))
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))

        # Quais personagens já escolhidos por outros slots
        taken_by = {}
        for j in range(self.n_players):
            if j != slot and self.choices[j]:
                taken_by[self.choices[j]] = j

        for idx, char in enumerate(CHARACTER_CATALOG):
            col_i = idx % cols
            row_i = idx // cols
            cx_   = start_x + col_i * (th + gap) + th // 2
            cy_   = self._GALL_TOP + row_i * row_h + th // 2 + gap // 2 - self.scroll_y

            rect = pygame.Rect(cx_ - th//2, cy_ - th//2, th, th)

            # Só desenha se visível
            if rect.bottom < self._GALL_TOP or rect.top > self._GALL_BOT:
                self._gallery_rects.append((idx, rect))
                continue

            # Estado visual
            is_chosen = (self.choices[slot] == char["key"])
            takenby   = taken_by.get(char["key"])

            # Sombra do card
            sh_rect = rect.move(0, 4)
            pygame.draw.rect(surf, (15, 10, 35), sh_rect, border_radius=12)

            # Fundo do card
            if is_chosen:
                bg_c  = PC[slot]
                brd_c = WHITE
            elif takenby is not None:
                bg_c  = _TAKEN
                brd_c = PL[takenby]
            else:
                bg_c  = (54, 42, 86)
                brd_c = (80, 65, 120)

            pygame.draw.rect(surf, bg_c,  rect, border_radius=12)
            pygame.draw.rect(surf, brd_c, rect, 2, border_radius=12)

            # Thumbnail
            img = _load_char_img(char["key"], th - 8)
            surf.blit(img, (rect.x + 4, rect.y + 4))

            # Badge "já escolhido" por outro jogador
            if takenby is not None and not is_chosen:
                badge_r = pygame.Rect(rect.right - 22, rect.top - 2, 22, 22)
                pygame.draw.circle(surf, PC[takenby],
                                   badge_r.center, 11)
                pygame.draw.circle(surf, WHITE, badge_r.center, 11, 2)
                _txt(surf, str(takenby + 1), F_XSM, WHITE,
                     badge_r.centerx, badge_r.centery)

            # Check mark se selecionado
            if is_chosen:
                ck = pygame.Rect(rect.right - 22, rect.top - 2, 22, 22)
                pygame.draw.circle(surf, _GREEN, ck.center, 11)
                pygame.draw.circle(surf, WHITE,  ck.center, 11, 2)
                _txt(surf, "✓", F_XSM, WHITE, ck.centerx, ck.centery)

            # Nome abaixo
            name_y = cy_ + th // 2 + 12
            _txt(surf, char["name"], F_XSM,
                 WHITE if (is_chosen or takenby is None) else _DIM,
                 cx_, name_y)

            self._gallery_rects.append((idx, rect))

        surf.set_clip(None)

        # Scrollbar discreta
        if content_h > (self._GALL_BOT - self._GALL_TOP):
            bar_h  = int((self._GALL_BOT - self._GALL_TOP) ** 2 / content_h)
            bar_y  = self._GALL_TOP + int(
                self.scroll_y * (self._GALL_BOT - self._GALL_TOP - bar_h) / max_scroll
            ) if max_scroll else self._GALL_TOP
            pygame.draw.rect(surf, (80, 68, 110),
                             (W - 8, self._GALL_TOP, 6, self._GALL_BOT - self._GALL_TOP),
                             border_radius=3)
            pygame.draw.rect(surf, (140, 120, 180),
                             (W - 8, bar_y, 6, bar_h), border_radius=3)

        # Botão Voltar
        self._btn_back = _btn(surf, "← Voltar", F_SM,
                              20, H - 56, 130, 40,
                              (60, 48, 95), (90, 72, 140))

        # Botão Confirmar (se já escolheu)
        if self.choices[slot]:
            char = next((c for c in CHARACTER_CATALOG
                         if c["key"] == self.choices[slot]), None)
            lbl  = f"✓ Confirmar {char['name']}" if char else "✓ Confirmar"
            self._btn_confirm = _btn(surf, lbl, F_SM,
                                     W - 230, H - 56, 210, 40,
                                     _GREEN, _GREEN_D)
        else:
            self._btn_confirm = None

    def _handle_gallery(self, event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_LEFT):
                self.screen = "setup"
            elif event.key == pygame.K_RETURN:
                self.screen = "setup"

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 30
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if hasattr(self, "_btn_back") and self._btn_back.collidepoint(mx, my):
                self.screen = "setup"
                return None

            if hasattr(self, "_btn_confirm") and self._btn_confirm and \
                    self._btn_confirm.collidepoint(mx, my):
                self.screen = "setup"
                return None

            if hasattr(self, "_btn_random") and self._btn_random.collidepoint(mx, my):
                self.choices[self.pick_slot] = None
                self.screen = "setup"
                return None

            for idx, rect in self._gallery_rects:
                if rect.collidepoint(mx, my):
                    char = CHARACTER_CATALOG[idx]
                    self.choices[self.pick_slot] = char["key"]
                    # Confirma imediatamente e volta
                    self.screen = "setup"
                    return None

        return None