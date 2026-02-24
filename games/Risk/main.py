import pygame as pg
import sys
from src.game import Game

from src.bot_versions.oldmcts import OldMCTS
from src.bot_versions.newmcts import NewMCTS
bot_versions = [OldMCTS, NewMCTS]

pg.init()
pg.mixer.init()
pg.font.init()
pg.event.set_grab(True)

WIDTH = 1280
HEIGHT = 720

window_size = pg.Vector2(WIDTH, HEIGHT)
screen = pg.display.set_mode(window_size, pg.RESIZABLE)

clock = pg.time.Clock()

pg.display.set_caption("Risk")

game = Game(clock, bot_versions, screen)
game.run()

pg.quit()
sys.exit()