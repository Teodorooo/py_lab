import pygame as pg
import pygame_gui
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
        self.font_path = "Risk/font/EraserRegular.ttf"
        
        self.width = screen.size[0]
        self.height = screen.size[1]
        
        self.playing = True
        self.scroll = 0
        self.settings_selected = False
        self.ui_manager = pygame_gui.UIManager((self.width, self.height))
        
        self.event_1 = pg.USEREVENT + 100
        pg.time.set_timer(self.event_1, 500)
        self.is_timer_on = False
        
        self.manage_cards = ManageCards(screen)

        self.mouse_clicked = False

    def init_game(self):
        players = self.manage_cards.players
        self.countries = MakeCountries(players).countries
        self.manage_players = PlayerManager(self.screen, players, self.countries, self.bot_versions, self.font_path)
        self.draw = Draw(self.screen, self.countries, self.font_path) 
        
    def run(self) -> None:
        while self.playing:
            self.screen.fill((60, 60, 60))
            self.events()
            mouse_pos = pg.Vector2(pg.mouse.get_pos())
            
            if not self.manage_cards.settings_selected:
                self.manage_cards.draw_cards(self.screen, self.width, self.height, self.mouse_clicked, self.is_timer_on, self.font_path)
                self.ui_manager.draw_ui(self.screen)
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
            pg.display.update()
            
    def win_screen(self, winning_player):
        self.screen.fill(winning_player.color)
        draw_text(self.screen, self.font_path, 20,
                  f'{winning_player.player_name} won !',
                  (0, 0, 0), self.width / 2, self.height / 2, center=True)
    
    def events(self) -> None:
        time_delta = self.clock.tick(60) / 1000.0
        for event in pg.event.get():
            if event.type == pg.VIDEORESIZE:
                self.width, self.height = event.size
                self.screen = pg.display.set_mode((self.width, self.height), pg.RESIZABLE)
                self.ui_manager.set_window_resolution((self.width, self.height))
                self.ui_manager.clear_and_reset()
                self.manage_cards.card_size_updated = True

            if event.type == pg.QUIT:
                self.playing = False

            self.mouse_clicked = (event.type == pg.MOUSEBUTTONDOWN)

            if event.type == pg.MOUSEWHEEL:
                self.scroll = event.dict['y']
                
            if event.type == self.event_1:
                self.is_timer_on = not self.is_timer_on

            if event.type == pg.KEYDOWN:
                self.manage_cards.change_player_name(pg.key.name(event.key))
                
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                self.manage_cards.ui_event = event
                
            if event.type == pygame_gui.UI_COLOUR_PICKER_COLOUR_PICKED:
                self.manage_cards.colour_picked(event.colour)
                
            if event.type == pygame_gui.UI_WINDOW_CLOSE:
                self.manage_cards.close_ui()
                
            self.ui_manager.process_events(event)

        self.ui_manager.update(time_delta)

        

            


