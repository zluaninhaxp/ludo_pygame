"""
main.py — Entry point do Ludo.

Estrutura de arquivos:
  main.py       Loop principal, eventos globais
  constants.py  Layout, paleta, caminhos (MPATH, HSTRETCH, SAFE…)
  piece.py      Classes Piece e Player
  game.py       Lógica de jogo (Game)
  board.py      Desenho do tabuleiro
  renderer.py   Desenho das peças, dado, painel lateral, telas
  menu.py       Tela de configuração

Controles:
  ESPAÇO  → rolar dado (jogador humano)
  clique  → selecionar peça a mover
  R       → reiniciar (volta ao menu)
"""
import sys
import pygame

from constants import W, H, FPS, BG, SIDE_W
from board    import draw_board
from renderer import draw_pieces, draw_sidebar, draw_end_screen
from menu     import Menu


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Ludo")
    clock  = pygame.time.Clock()

    menu = Menu()
    game = None

    while True:
        dt = clock.tick(FPS)   # ms desde o último frame

        # ── Eventos ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if game is None:
                # Tela de menu
                result = menu.handle(event)
                if result == "start":
                    game = menu.make_game()
            else:
                # Tela de jogo
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        menu = Menu()
                        game = None
                        continue
                    if (event.key == pygame.K_SPACE
                            and game.phase == "roll"
                            and game.cp().human
                            and game.dice_spin == 0):
                        game.start_roll()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    game.click(*event.pos)

        # ── Atualização ───────────────────────────────────────────────────────
        if game is not None:
            game.update(dt)

        # ── Renderização ──────────────────────────────────────────────────────
        screen.fill(BG)

        if game is None:
            menu.draw(screen)
        else:
            draw_board(screen)
            draw_pieces(screen, game)
            draw_sidebar(screen, game)
            if game.phase == "end":
                draw_end_screen(screen, game)

        pygame.display.flip()


if __name__ == "__main__":
    main()
