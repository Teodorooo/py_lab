import pygame as pg
import asyncio
from src.draw import Draw
from src.country import MakeCountries, Country
from src.gui import ManageCards
from src.player import PlayerManager
from src.utils import Utils
draw_text = Utils().draw_text

class Game:
    def __init__(self, clock: pg.time.Clock, bot_versions: list, screen: object) -> None:
        self.clock = clock
        self.bot_versions = bot_versions
        
        self.screen = screen
        self.font_path = "font/EraserRegular.ttf"
        
        self.width, self.height = screen.get_size()
        
        self.playing = True
        self.scroll = 0
        self.settings_selected = False
        
        self.is_timer_on = False
        self.timer_last_toggle = pg.time.get_ticks()
        
        self.manage_cards = ManageCards(screen)

        self.mouse_clicked = False

    def init_game(self):
        players = self.manage_cards.players
        self.countries = MakeCountries(players).countries
        self.manage_players = PlayerManager(self.screen, players, self.countries, self.bot_versions, self.font_path)
        self.draw = Draw(self.screen, self.countries, self.font_path) 
        
    async def run(self) -> None:
        while self.playing:
            current_width, current_height = self.screen.get_size()
            if (current_width, current_height) != (self.width, self.height):
                self.width, self.height = current_width, current_height
                self.manage_cards.card_size_updated = True

            self.screen.fill((60, 60, 60))
            self.events()
            mouse_pos = pg.Vector2(pg.mouse.get_pos())
            now = pg.time.get_ticks()
            
            if now - self.timer_last_toggle >= 500:
                self.is_timer_on = not self.is_timer_on
                self.timer_last_toggle = now
                
            if not self.manage_cards.settings_selected:
                self.manage_cards.draw_cards(self.screen, self.width, self.height, self.mouse_clicked, self.is_timer_on, self.font_path)
                if self.manage_cards.settings_selected:
                    self.init_game()
            else:
                for country in self.countries:
                    country.check_hovered(mouse_pos, self.draw.mouse_offset, self.mouse_clicked, self.screen, self.font_path)
                self.draw.update()
                self.manage_players.handle_player_turns(self.mouse_clicked, self.scroll)
                player_won = self.manage_players.check_player_wins(len(self.countries))
                if player_won:
                    self.win_screen(player_won)

            self.scroll = 0
            self.mouse_clicked = False
            
            await asyncio.sleep(0)
            pg.display.update()
            
    def win_screen(self, winning_player):
        self.screen.fill(winning_player.color)
        draw_text(self.screen, self.font_path, 20,
                  f'{winning_player.player_name} won !',
                  (0, 0, 0), self.width / 2, self.height / 2, center=True)
    
    def events(self) -> None:
        self.clock.tick(60)
        for event in pg.event.get():
            if event.type == pg.VIDEORESIZE:
                self.width, self.height = event.size
                self.screen = pg.display.set_mode((self.width, self.height), pg.RESIZABLE)
                self.manage_cards.card_size_updated = True

            if event.type == pg.QUIT:
                self.playing = False

            self.mouse_clicked = (event.type == pg.MOUSEBUTTONDOWN)

            if event.type == pg.MOUSEWHEEL:
                self.scroll = event.dict['y']

            if event.type == pg.KEYDOWN:
                self.manage_cards.change_player_name(pg.key.name(event.key))
