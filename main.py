import sys
import pygame
import constants  # importamos o módulo todo para chamar constants.resize()

from constants import FPS, BG
from board     import draw_board
from renderer  import draw_pieces, draw_sidebar, draw_end_screen
from menu      import Menu


def _initial_size():
    """Retorna (~70 % da altura da tela) forçando uma proporção mais larga (16:9)."""
    pygame.display.init()
    info = pygame.display.Info()
    sw, sh = info.current_w, info.current_h
    
    scale = 0.70
    h = int(sh * scale) & ~15          # Mantém a altura legal que você gostou
    
    # MÁGICA AQUI: A largura agora é calculada para ser no formato Widescreen (16:9)
    w = int(h * (16 / 9)) & ~15
    
    # Garante que não vai estourar o monitor do jogador
    w = min(w, int(sw * 0.9) & ~15)
    
    # Largura mínima de 850 para não espremer os cards se a tela for pequena
    return max(w, 850), max(h, 480)


def main():
    pygame.init()

    # ── Tamanho inicial ───────────────────────────────────────────────────────
    init_w, init_h = _initial_size()
    constants.resize(init_w, init_h)

    screen = pygame.display.set_mode(
        (init_w, init_h),
        pygame.RESIZABLE
    )
    pygame.display.set_caption("Ludo")
    clock    = pygame.time.Clock()
    fullscreen = False

    menu = Menu()
    game = None

    while True:
        dt = clock.tick(FPS)

        # ── Eventos ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ESC fecha
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            # F11 / Alt+Enter — toggle fullscreen
            if event.type == pygame.KEYDOWN and (
                event.key == pygame.K_F11
                or (event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT))
            ):
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode(
                        (init_w, init_h), pygame.RESIZABLE
                    )
                w, h = screen.get_size()
                constants.resize(w, h)
                # Recria o menu para recalcular posições dos botões
                if game is None:
                    menu = Menu()

            # Janela redimensionada pelo usuário (arrastar borda)
            if event.type == pygame.VIDEORESIZE:
                w, h = event.w, event.h
                screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                constants.resize(w, h)
                if game is None:
                    menu = Menu()

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
        w, h = screen.get_size()
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