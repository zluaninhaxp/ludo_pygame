"""
menu.py — Tela de configuração da partida.

Permite escolher de 2 a 4 jogadores.
Jogador 1 (Vermelho) é sempre Humano.
Os demais podem ser alternados entre Humano e CPU.
"""
import pygame
from constants import W, H, BG, PC, PL, PN, DGRAY, WHITE, LGRAY
from piece import Player

pygame.font.init()
F_BIG = pygame.font.SysFont("Arial", 36, bold=True)
F_MED = pygame.font.SysFont("Arial", 22, bold=True)
F_SM  = pygame.font.SysFont("Arial", 16)
F_XSM = pygame.font.SysFont("Arial", 13)


def _txt(surf, text, font, color, cx, cy, anchor="c"):
    img = font.render(str(text), True, color)
    r   = img.get_rect()
    if anchor == "c":  r.center  = (cx, cy)
    if anchor == "tl": r.topleft = (cx, cy)
    surf.blit(img, r)


class Menu:
    def __init__(self):
        self.n_players = 2
        # tipos para jogadores 1-3 (jogador 0 é sempre humano)
        self.types = ["human", "cpu", "cpu", "cpu"]

    # ── Desenho ───────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface):
        surf.fill(BG)

        # Título
        _txt(surf, "🎲  L U D O", F_BIG, (255, 220, 30), W//2, 60)
        _txt(surf, "Configuração da Partida", F_MED, (160, 160, 180), W//2, 105)

        # ── Número de jogadores ──
        row_y = 155
        _txt(surf, "Número de jogadores:", F_SM, WHITE, W//2 - 60, row_y)
        _txt(surf, str(self.n_players), F_BIG, WHITE, W//2 + 80, row_y)

        # Botões + e –
        for label, bx, action in [("▲", W//2 + 108, 1), ("▼", W//2 + 135, -1)]:
            color = (50, 150, 50) if action == 1 else (170, 50, 50)
            pygame.draw.rect(surf, color, (bx - 14, row_y - 14, 28, 28), border_radius=5)
            _txt(surf, label, F_XSM, WHITE, bx, row_y)

        # ── Linhas de jogador ──
        _txt(surf, "Jogador 1 — Vermelho — Humano (fixo)",
             F_XSM, PL[0], W//2, 205)

        for i in range(1, 4):
            y = 228 + i * 72
            if i >= self.n_players:
                pygame.draw.rect(surf, (35, 35, 55), (W//2 - 170, y, 340, 58), border_radius=8)
                _txt(surf, f"Jogador {i+1} — desativado", F_XSM, (80, 80, 100), W//2, y + 29)
                continue

            pygame.draw.rect(surf, (50, 50, 72), (W//2 - 170, y, 340, 58), border_radius=8)
            pygame.draw.rect(surf, PC[i],        (W//2 - 170, y, 340, 58), 2, border_radius=8)

            _txt(surf, f"Jogador {i+1} — {PN[i]}", F_SM, PC[i], W//2 - 50, y + 29)

            t   = self.types[i]
            col = (45, 155, 45) if t == "human" else (155, 45, 45)
            pygame.draw.rect(surf, col, (W//2 + 55, y + 10, 105, 38), border_radius=8)
            _txt(surf, "Humano" if t == "human" else "CPU",
                 F_SM, WHITE, W//2 + 107, y + 29)

        # ── Botão iniciar ──
        pygame.draw.rect(surf, (45, 155, 45),
                         (W//2 - 95, H - 112, 190, 52), border_radius=12)
        _txt(surf, "▶   INICIAR", F_MED, WHITE, W//2, H - 86)

        _txt(surf, "↑↓ = nº de jogadores   •   clique no botão para alternar tipo",
             F_XSM, (90, 90, 110), W//2, H - 42)

    # ── Eventos ───────────────────────────────────────────────────────────────
    def handle(self, event) -> str | None:
        """Retorna 'start' quando o jogo deve começar, None caso contrário."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.n_players = min(4, self.n_players + 1)
            elif event.key == pygame.K_DOWN:
                self.n_players = max(2, self.n_players - 1)
            elif event.key == pygame.K_RETURN:
                return "start"

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Botões ▲ ▼
            row_y = 155
            if W//2 + 94 <= mx <= W//2 + 122 and row_y - 14 <= my <= row_y + 14:
                self.n_players = min(4, self.n_players + 1)
            if W//2 + 121 <= mx <= W//2 + 149 and row_y - 14 <= my <= row_y + 14:
                self.n_players = max(2, self.n_players - 1)

            # Toggle Humano/CPU
            for i in range(1, 4):
                y = 228 + i * 72
                if i < self.n_players:
                    if W//2 + 55 <= mx <= W//2 + 160 and y + 10 <= my <= y + 48:
                        self.types[i] = "cpu" if self.types[i] == "human" else "human"

            # Botão iniciar
            if W//2 - 95 <= mx <= W//2 + 95 and H - 112 <= my <= H - 60:
                return "start"

        return None

    # ── Criar jogo ────────────────────────────────────────────────────────────
    def make_game(self):
        from game import Game
        players = [Player(0, True)]   # jogador 0 sempre humano
        for i in range(1, self.n_players):
            players.append(Player(i, self.types[i] == "human"))
        return Game(players)
