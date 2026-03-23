import asyncio
import pygame as pg
import sys

pg.init()
pg.mixer.init()
pg.font.init()

WIDTH = 1280
HEIGHT = 720

window_size = pg.Vector2(WIDTH, HEIGHT)
screen = pg.display.set_mode(window_size, pg.RESIZABLE)
clock = pg.time.Clock()
pg.display.set_caption("Risk")

async def main():
    try:
        from src.game import Game
        from src.bot_versions.oldmcts import OldMCTS
        from src.bot_versions.newmcts import NewMCTS
        bot_versions = [OldMCTS, NewMCTS]
        
        game = Game(clock, bot_versions, screen)
        await game.run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        # Draw the error on screen so we can see it
        font = pg.font.SysFont("monospace", 20)
        error_lines = traceback.format_exc().split('\n')
        screen.fill((0, 0, 0))
        for i, line in enumerate(error_lines):
            text = font.render(line, True, (255, 0, 0))
            screen.blit(text, (10, 10 + i * 25))
        pg.display.update()
        
        # Keep the error on screen
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
            await asyncio.sleep(0)

asyncio.run(main())