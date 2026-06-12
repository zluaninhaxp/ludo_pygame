import sys
import pygame

# Importamos as constantes necessárias
# Certifique-se de que BSIZE está em constants.py
from constants import W, H, FPS, BG, SIDE_W, BSIZE
from board     import draw_board
from renderer import draw_pieces, draw_sidebar, draw_end_screen
from menu     import Menu

def main():
    pygame.init()
    
    # Usamos RESIZABLE para você poder aumentar a janela e ver melhor os rostinhos
    screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
    pygame.display.set_caption("Ludo")
    clock  = pygame.time.Clock()

    menu = Menu()
    game = None

    while True:
        dt = clock.tick(FPS)

        # ── Eventos ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Fecha com ESC
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if game is None:
                result = menu.handle(event)
                if result == "start":
                    game = menu.make_game()
            else:
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
            # draw_board precisa das constantes carregadas corretamente
            draw_board(screen)
            draw_pieces(screen, game)
            draw_sidebar(screen, game)
            if game.phase == "end":
                draw_end_screen(screen, game)

        pygame.display.flip()

if __name__ == "__main__":
    main()