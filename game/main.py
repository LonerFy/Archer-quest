"""Point d'entrée. Ordinateur : `python main.py`. Web : `pygbag .` (voir README)."""
import asyncio
import traceback


def show_error(message):
    """Affiche l'erreur sur la page : dans le navigateur, la console est souvent invisible."""
    try:
        import pygame
        screen = pygame.display.get_surface() or pygame.display.set_mode((960, 600))
        screen.fill((20, 6, 6))
        font = pygame.font.Font(None, 22)
        for i, line in enumerate(message.strip().splitlines()[-18:]):
            screen.blit(font.render(line[:110], True, (255, 150, 150)), (16, 16 + i * 24))
        pygame.display.flip()
    except Exception:
        pass


async def main():
    try:
        from archer.app import App
        await App().run()
    except Exception:
        report = traceback.format_exc()
        print(report)
        show_error(report)
        while True:            # garde la page en vie pour lire le message
            await asyncio.sleep(0.2)


asyncio.run(main())
