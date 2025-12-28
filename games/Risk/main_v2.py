import json 
import pygame as pg
import sys
import pandas as pd
from shapely.geometry import Point, Polygon
from random import shuffle
import pygame_gui
from pygame_gui.elements import UIButton
from pygame_gui.windows import UIColourPickerDialog

from utils import Utils
utils = Utils()
draw_text = utils.draw_text
attack_calculation = utils.attack_calculation

from bot_versions.oldmtcs import OldMCTS
from bot_versions.newmcts import NewMCTS
bot_versions = [OldMCTS, NewMCTS]

class PlayerManager:
    def __init__(self, screen, players, countries, bot_versions, font_path):
        self.players = players
        self.countries = countries
        self.bot_versions = bot_versions
        self.screen = screen
        self.font_path = font_path
        self.turn = 1

        self.add_starting_units()
        self.assign_playing_order()

        self.player_objects = []
        self.create_player_objects()
        
        self.starting_phase = True
    
    def create_player_objects(self):
        for player, player_info in self.players.items():
            if player_info['bot_version']:
                for version in self.bot_versions:
                    if version.__name__.lower() == player_info['bot_version'].lower():
                        self.player_objects.append(BotPlayer(self.screen, self.countries, player, self.players, self.font_path, version.__name__, version))
            else:
                self.player_objects.append(HumanPlayer(self.screen, self.countries, player, self.players, self.font_path))
                
    def handle_player_turns(self, mouse_clicked, scroll):
        finished_starting_phase = []
        current_player = self.player_objects[self.turn - 1]
        if self.starting_phase:
            for player in self.player_objects:
                if player.available_units == 0:
                    finished_starting_phase.append(True)
                else:
                    finished_starting_phase.append(False)
            if all(finished_starting_phase):
                self.starting_phase = False

        if isinstance(current_player, HumanPlayer):
            current_player.human_play(mouse_clicked, scroll, self.starting_phase) 
        else:
            current_player.bot_play(self.starting_phase, )
        
        if current_player.end_turn:
            self.turn = (self.turn % len(self.player_objects)) + 1

    def add_starting_units(self) -> None:
        for player_info in self.players.values():
            player_info['available_units'] = (40 - (len(self.players) - 2) * 5) - 30
    
    def assign_playing_order(self):
        player_keys = list(self.players.keys())
        shuffle(player_keys)

        for i, player_name in enumerate(player_keys):
            self.players[player_name]['playing_order'] = i + 1

    def check_player_wins(self, all_countries) -> object:
        for player in self.player_objects:
            if len(player.controlled_countries) == all_countries:
                return player
        return None

class Player:
    def __init__(self, screen, countries, player_name, players, font_path):
        self.player_name = player_name
        self.players = players
        self.countries = countries
        self.screen = screen
        self.font_path = font_path
        self.phase = 'place'
        
        self.width = screen.size[0]
        self.height = screen.size[1]

        for player, player_info in players.items():
            if player == self.player_name:
                self.color = player_info['color']
                self.playing_order = player_info['playing_order']
                self.available_units = player_info['available_units']

        self.attacker = None
        self.defender = None
        self.deployed_units = 0
        self.attack_confirmed = False

        self.country_a = None
        self.country_b = None

        self.fortified = False
        self.new_army_received = False
        self.end_turn = False
        
        self.update_controlled_countries()
        
    def update_turn(self):
        if not self.starting_phase:                                              
            if self.phase == 'place':                                                        
                self.phase = 'attack'                                                        
                self.end_turn = False                                                        
            elif self.phase == 'attack':                                                         
                self.phase = 'fortify'                                                       
                self.end_turn = False                                                        
                self.fortified = False                                                        
            else:                                               
                self.phase = 'place'                                                         
                self.end_turn = True                                                 
                self.new_army_received = False  

    def update_army(self):
        if not self.new_army_received:
            new_army = int(len(self.controlled_countries) / 3)
            self.available_units += new_army if new_army > 3 else 3
            self.new_army_received = True
            
    def update_controlled_countries(self):
        updated_countries = {}
        for player, player_info in self.players.items():
            for country in self.countries:
                if country.owner == player: 
                    if player in updated_countries:
                        updated_countries[player].append(country)
                    else:
                        updated_countries[player] = [country]
        
            for updated_player, countries in updated_countries.items():
                if updated_player == player:
                    player_info['controlled_countries'] = countries
                if self.player_name == updated_player:
                    self.controlled_countries = countries
                    player_info['available_units'] = self.available_units                  
                    
    def draw_player_and_phase(self):
        draw_text(self.screen, self.font_path, 20, f"{self.player_name}'s turn", (0, 0, 0), 10, self.height/2, rect_color=self.color)
        draw_text(self.screen, self.font_path, 20, f"Army: {self.available_units}", (0, 0, 0), 10, self.height/1.75, rect_color=self.color)
        draw_text(self.screen, self.font_path, 20, f"Phase: {self.phase}", (255,255,255), 10, self.height/1.5)
                         
class HumanPlayer(Player):
    def __init__(self, screen, countries, player_name, players, font_path):
        super().__init__(screen, countries, player_name, players, font_path)

    def human_play(self, mouse_clicked, scroll, starting_phase):
        self.end_turn = False
        self.starting_phase = starting_phase        
        self.mouse_clicked = mouse_clicked
        self.scroll = scroll
        
        super().draw_player_and_phase()
        self.update_army()
        
        if self.phase == 'place':
            self.place()
        elif self.phase == 'attack':
            self.attack()
        else:
            if not self.fortified:
                self.fortify()
                
        self.check_turn_end()
                  
    def check_turn_end(self) -> None:                                                      
        button_hovered = draw_text(self.screen, self.font_path, 20, ' Next Phase ', (200, 200, 255), 25, 25, rect_color = (0, 100, 0), get_hovered = True)                                                        
        if self.mouse_clicked and not self.attack_confirmed and button_hovered:                                                      
            super().update_turn()
                                                                               
    def place(self):                                                      
        for country in self.controlled_countries:                                                      
            if country.selected and self.available_units > 0:                                                      
                country.units += 1                                                      
                self.available_units -= 1                                                      
                if self.starting_phase:                                                      
                    self.end_turn = True

    def select_fighting_countries(self) -> bool:
        self.deployed_units += self.scroll
        if self.deployed_units < 1: self.deployed_units = 1
        if self.deployed_units > 3: self.deployed_units = 3
        
        for country in self.countries:
            if country.selected:
                if country in self.controlled_countries: 
                    if country.units > 1:
                        self.attacker = country
                elif self.attacker:
                    self.defender = country if country in self.attacker.neighbours else None
        
        if self.attacker:
            sending_cap = self.attacker.units if self.attacker.units < 4 else 4
            if self.deployed_units >= sending_cap:
                self.deployed_units = sending_cap - 1
        
        button_is_hovered = draw_text(self.screen, self.font_path, 20, f'{self.attacker.name if self.attacker else '(attacker)'} attacks {self.defender.name if self.defender else '(defender)'} with {self.deployed_units} units, click to confirm.', (200, 200, 255), 10, self.height - 50, rect_color = (0, 100, 0), get_hovered = True)    

        if self.mouse_clicked and self.attacker and self.defender and button_is_hovered:
            return True
        else:
            return False

    def check_connected(self, country_b):
        if self.country_a == country_b:
            return True
        
        visited = set()
        queue = [self.country_a]
        
        while queue:
            current = queue.pop(0)
            if current == country_b:
                return True 
            if current not in visited:
                visited.add(current)      
                queue.extend([
                    neighbor for neighbor in self.countries
                    if neighbor in current.neighbours and neighbor.owner == self.player_name
                ])
                
        return False
        
    def calculate_attack_outcome(self):
        self.deployed_units += self.scroll
        if self.deployed_units < 1: self.deployed_units = 1
        
        self.defender.units, self.attacker.units = attack_calculation(self.deployed_units, self.defender.units, self.attacker.units)
            
        if self.defender.units <= 0:
            self.defender.original_color = self.attacker.original_color
            self.defender.change_color_when_hovered()
            self.defender.owner = self.attacker.owner
            
            if self.deployed_units >= self.attacker.units: self.deployed_units = self.attacker.units - 1
            button_is_hovered = draw_text(self.screen, self.font_path, 20, f'Send {self.deployed_units} units to {self.defender.name}, click to confirm', (200, 200, 255), 10, self.height - 50, rect_color = (0, 100, 0), get_hovered = True)
            if button_is_hovered and self.mouse_clicked:
                self.defender.units = self.deployed_units
                self.attacker.units -= self.deployed_units
                self.reset_vars()
        else:
            self.reset_vars()       
        
    def attack(self):
        if self.attack_confirmed:
            self.calculate_attack_outcome()
        else:
            self.attack_confirmed = self.select_fighting_countries()

    def fortify(self):
        self.deployed_units += self.scroll
        if self.deployed_units < 1: self.deployed_units = 1
        if self.country_a and self.deployed_units >= self.country_a.units: self.deployed_units = self.country_a.units - 1
        
        for country in self.controlled_countries:
            if country.selected:
                if not self.country_a:
                    self.country_a = country if country.units > 1 else None
                elif not self.country_b:
                    self.country_b = country if self.check_connected(country) and country != self.country_a else None
                else:
                    self.country_a = country if country.units > 1 else None
                    self.country_b = None
                    
        button_is_hovered = draw_text(self.screen, self.font_path, 20, f'Move {self.deployed_units} units from {self.country_a.name if self.country_a else '(Country A)'} to {self.country_b.name if self.country_b else '(Country B)'}, click to confirm', (200, 200, 255), 10, self.height - 50, rect_color = (0, 100, 0), get_hovered = True)
        
        if self.country_a and self.country_b:
            if button_is_hovered and self.mouse_clicked:
                self.country_a.units -= self.deployed_units
                self.country_b.units += self.deployed_units
                self.fortified = True
    
    def reset_vars(self):
        self.attack_confirmed = False
        self.attacker = None
        self.defender = None
        super().update_controlled_countries()  
    
class BotPlayer(Player):
    def __init__(self, screen, countries, player_name, players, font, bot_version, bot):
        super().__init__(screen, countries, player_name, players, font)
        
        self.player_index = self.players[player_name]['playing_order']
        self.conquered_country = None
        self.bot_version = bot_version
        self.bot = bot
        
    def bot_play(self, starting_phase):
        self.end_turn = False
        self.starting_phase = starting_phase

        if self.phase == "place" and not self.new_army_received:
            self.update_army()  # add units if it's a new turn

        self.update_controlled_countries()

        bot =  self.bot(self.players, self.countries, self.starting_phase, self.player_index, self.phase, self.fortified, self.conquered_country)
        
        action = bot.get_action()
        
        action_type = action[0]
        # print(action)

        if self.conquered_country:
            for country in self.countries:
                if country.name == action[1]:   # from country:
                    country.units -= action[-1] # - units
                if country.name == action[2]:   # to country:
                    country.units += action[-1] # + units
            self.conquered_country = None
            self.phase = "attack"

        elif action_type == "place":
            for country in self.controlled_countries:
                if country.name == action[1]:         # place country
                    self.available_units -= action[2] # - units
                    country.units += action[2]        # + units
            if self.starting_phase:
                self.end_turn = True
            elif self.available_units <= 0:
                self.phase = "attack"

        elif action_type == "attack":
            attacker = None
            defender = None
            for country in self.countries:
                if country.name == action[1]: # attacker
                    attacker = country
                if country.name == action[2]: # defender
                    defender = country

            if attacker and defender:
                defender.units, attacker.units = attack_calculation(
                    action[3], # units
                    defender.units, 
                    attacker.units
                )
                if defender.units == 0:
                    self.conquered_country = {
                        "type": "conquered",
                        "from": attacker.name,
                        "to": defender.name,
                    }
                    defender.owner = self.player_name
                    defender.color = self.color
                    defender.original_color = self.color

        elif action_type == "fortify":
            if not self.fortified:
                for country in self.countries:
                    if country.name == action[1]:  # from country:
                        country.units -= action[3] # - units
                    if country.name == action[2]:  # to country:
                        country.units += action[3] # + units
                self.fortified = True
                self.end_turn = True

        else: # skip_phase
            if action_type == "skip_to_attack":
                self.phase = "attack"
            elif action_type == "skip_to_fortify":
                self.phase = "fortify"
                self.fortified = False
            elif action_type == "end_turn" or action == "end_turn": 
                self.end_turn = True
                self.phase = "place"
                self.new_army_received = False

        self.update_controlled_countries()
        super().draw_player_and_phase()

class Draw:
    def __init__(self, screen, countries, font_path):
        self.screen = screen
        self.countries = countries
        self.font_path = font_path
        
        self.mouse_offset = pg.Vector2(3650, 395)
        self.offset_mouse_pos = pg.Vector2()
        self.mouse_pos = pg.Vector2(0, 0)

    def update_camera(self) -> None:
        mouse_pressed = pg.mouse.get_pressed()
        mouse_pos = pg.mouse.get_pos()
        
        if mouse_pressed[0]:
            
            self.offset_mouse_pos.xy = mouse_pos[0], mouse_pos[1]
            
            self.mouse_offset.x = self.mouse_offset.x + (self.offset_mouse_pos.x - self.mouse_pos.x)*-1
            self.mouse_offset.y = self.mouse_offset.y + (self.offset_mouse_pos.y - self.mouse_pos.y)*-1
        
        self.mouse_pos.xy = mouse_pos[0], mouse_pos[1]
    
    def draw_countries(self) -> None:
        for country in self.countries:
            pg.draw.polygon(
                self.screen,
                country.color,
                [(x - self.mouse_offset.x, y - self.mouse_offset.y) for x, y in country.coords],
            )
            pg.draw.polygon(
                self.screen,
                (255, 255, 255),
                [(x - self.mouse_offset.x, y - self.mouse_offset.y) for x, y in country.coords],
                width=1,
            )
    
    def draw_units(self):
        for country in self.countries:
            draw_text(self.screen, self.font_path, 10, str(country.units), (0, 0, 0), country.center.x - self.mouse_offset.x, country.center.y - self.mouse_offset.y, center = True)
            
    def update(self):
        self.update_camera()
        self.draw_countries()
        self.draw_units()

class Country:
    def __init__(self, name, owner, coords, color):
        self.name = name
        self.owner = owner
        self.coords = coords
        self.original_color = color
        self.color = color
        self.polygon = Polygon(self.coords)
        self.units = 1
        self.hovered = False
        self.selected = False
        self.neighbours = []
        self.center = self.get_center()

    def change_color_when_hovered(self):
        if self.hovered:

            self.color = [min(c + 50, 255) for c in self.original_color]
        else:

            self.color = self.original_color

    def check_hovered(self, mouse_pos: pg.Vector2, mouse_offset: pg.Vector2, mouse_clicked: bool) -> None:
        self.selected = self.hovered and mouse_clicked
        is_hovering = Point(mouse_pos.x + mouse_offset.x, mouse_pos.y + mouse_offset.y).within(self.polygon)

        if is_hovering != self.hovered:
            self.hovered = is_hovering
            self.change_color_when_hovered()

    def get_center(self) -> pg.Vector2:
        return pg.Vector2(
            pd.Series([x for x, y in self.coords]).mean(),
            pd.Series([y for x, y in self.coords]).mean(),
        )

class MakeCountries:
    def __init__(self, players):
        self.MAP_WIDTH = 2.05 * 4000
        self.MAP_HEIGHT = 1.0 * 4000
        self.players = players
        self.countries = []
        self.read_geo_data()
        self.assign_countries_to_player()
        self.create_countries()
        for country in self.countries:
            self.get_country_neighbours(country)    
        
    def create_countries(self) -> None:
        for name, coords in self.geo_data.items():
            for owner, info in self.players.items():
                for country_name in info['controlled_countries']:
                    if country_name == name:
                        xy_coords = []
                        for coord in coords:
                            x = (self.MAP_WIDTH / 360) * (180 + coord[0])
                            y = (self.MAP_HEIGHT / 180) * (90 - coord[1])
                            xy_coords.append(pg.Vector2(x, y))
                        self.countries.append(Country(name, owner, xy_coords, info['color']))

    def assign_countries_to_player(self) -> None:
        all_starting_countries = list(self.geo_data.keys())
        shuffle(all_starting_countries)      
        num = 0
        
        for player_info in self.players.values():
            player_info["controlled_countries"] = all_starting_countries[
                int(num) : int(len(all_starting_countries) / len(self.players) + num)]
            num += len(all_starting_countries) / len(self.players) 
        
    def read_geo_data(self) -> None:
        with open("data/country_coords.json", "r") as f:
            self.geo_data = json.load(f)
            
    def get_country_neighbours(self, country: Country) -> dict:
        for other_country in self.countries:
            if country.name != other_country.name:
                if country.polygon.intersects(other_country.polygon):
                    country.neighbours.append(other_country)
                    
        overrides = {
            "United Kingdom": ["Ireland", "France", "Iceland"],
            "France": ["United Kingdom"],
            "Ireland": ["United Kingdom", "Iceland"],
            "Iceland": ["United Kingdom", "Ireland"],
            "Denmark": ["Norway", "Sweden"],
            "Norway": ["Denmark"],
            "Sweden": ["Denmark"],
            "Finland": ["Estonia"],
            "Estonia": ["Finland"],
        }
        name_to_country = {c.name: c for c in self.countries}
        
        if country.name in overrides:
            for neighbor_name in overrides[country.name]:
                if neighbor_name in name_to_country:
                    country.neighbours.append(name_to_country[neighbor_name])

class ManageCards: 
    def __init__(self, screen, ui_manager):
        self.x_divisions = 3
        self.y_divisions = 2
        self.player_count = 2
        self.player_cards = [PlayerCard(ui_manager, screen, self.x_divisions, self.y_divisions, n) for n in range(self.player_count)]
        self.player_count -= 1
        self.ui_manager = ui_manager
        self.screen = screen
        self.changed_card_name = None
        self.card_size_updated = False
        self.ui_event = None
        self.settings_selected = False
        
    def draw_cards(self, screen, width, height, mouse_clicked, is_timer_on, font_path):
        mouse_pos = pg.Vector2(pg.mouse.get_pos())

        if self.card_size_updated:
            for card in self.player_cards:
                self.update_card_size(card, width, height)
            self.card_size_updated = False

        for card in self.player_cards:
            card.draw_card(screen, is_timer_on, mouse_clicked, font_path, mouse_pos)

            if getattr(card, "name_selected_this_frame", False):
                self.changed_card_name = card

            if self.ui_event:
                self.open_ui(card)

        self.add_button(screen, width, height, mouse_clicked, font_path, "Add Player", self.player_count + 1, self.add_player)
        self.add_button(screen, width, height, mouse_clicked, font_path, "Start", self.y_divisions * self.x_divisions - 1, self.start_game)
        
    def start_game(self, _):
        self.settings_selected = True
        self.players = {f'{card.name}': {"bot_version": None if card.type == "human" else "newmcts", "color": (card.color.r, card.color.g, card.color.g)} for card in self.player_cards} 

    def open_ui(self, card):
        if hasattr(card, "colour_picker_button") and self.ui_event.ui_element == card.colour_picker_button:
            self.changed_card_color = card

            x, y, w, h = card.picked_color_surf

            w = max(int(w), 390)
            h = max(int(h), 390)

            self.colour_picker = UIColourPickerDialog(
                pg.Rect(int(x), int(y), w, h),
                card.ui_manager,
                window_title="Change Colour...",
                initial_colour=pg.Color(255, 255, 255)
            )
            card.colour_picker_button.disable()

            self.ui_event = None

    def update_card_size(self, card, width, height):
        card.update_card_coords(width, height, self.x_divisions, self.y_divisions)
        card.kill_button = True
        card.draw_button_once_flag = True
        card.xy_pos_updated = False
        
    def add_button(self, screen, width, height, mouse_clicked, font_path, text, pos, func):
        topleft, topright, bottomleft, bottomright = get_card_coords(width, height, self.x_divisions, self.y_divisions, pos)
        shrink_amount = (width + height) * 0.015        
        
        coords = (topleft.xy + (shrink_amount, shrink_amount),
                 topright.xy + (-shrink_amount, shrink_amount), 
                 bottomright.xy + (-shrink_amount, -shrink_amount), 
                 bottomleft.xy + (shrink_amount, -shrink_amount))
        
        shrink_amount *= 2
        
        pg.draw.polygon(screen, "black", coords, 5)
        
        draw_text(screen,
                  font_path,
                  shrink_amount,
                  text,
                  "black",
                  (topleft.x) + shrink_amount * 1.5,
                  (topleft.y) + shrink_amount * 1.2)
        
        mouse_pos = pg.Vector2(pg.mouse.get_pos())
        
        button = Polygon(coords)
        
        if Point(mouse_pos.x, mouse_pos.y).within(button):
            if mouse_clicked:
                func(screen)
                
    def add_player(self, screen):
        self.player_count += 1
        if self.x_divisions * self.y_divisions - 2 == self.player_count:
            if self.player_count == self.x_divisions * self.y_divisions - 2:
                if self.x_divisions - self.y_divisions >= 2: 
                    self.y_divisions += 1
                else:         
                    self.x_divisions += 1
                self.card_size_updated = True
                
        new_player = PlayerCard(self.ui_manager, screen, self.x_divisions, self.y_divisions, self.player_count)
        self.player_cards.append(new_player)
        
    def colour_picked(self, color):
        self.changed_card_color.color = color
        
    def close_ui(self):
        if hasattr(self, "changed_card_color") and self.changed_card_color:
            self.changed_card_color.colour_picker_button.enable()
        self.colour_picker = None
        
    def change_player_name(self, key):
        if not self.changed_card_name:
            return

        card = self.changed_card_name

        if not getattr(card, "is_changing_name", False):
            return

        key_fits = card.name_txt_rect.topright[0] < card.topright.x - card.shrink_amount
        
        if key == "backspace":
            card.name = card.name[:-1]
        elif key == "space":
            if key_fits:
                card.name += " "
        elif len(key) > 1:
            return
        else:
            if getattr(card, "name_txt_rect", None) is not None:
                if key_fits:
                    card.name += key
            else:
                card.name += key

        if getattr(card, "name_info", None) is not None:
            card.name_info.value = card.name
            card.name_info._pos_left_once = False 


class PlayerCard:
    def __init__(player, ui_manager, screen, x_divisions, y_divisions, player_num ,name = "Pick Name", color = pg.Color(0, 0, 0), type = None, is_bot = True, version = None):
        player.screen = screen
        player.name = name
        player.ui_manager = ui_manager
        player.color = color
        player.type = type
        player.is_bot = is_bot
        player.version = version
        player.num = player_num
        player.ui_manager = ui_manager
        player.x_divisions = x_divisions
        player.y_divisions = y_divisions
        player.kill_button = False
        player.draw_button_once_flag = True
        player.is_changing_name = False
        player.xy_pos_updated = False

        player.name_info = None
        player.name_txt_rect = None
        player.name_selected_this_frame = False

        player.update_card_coords(screen.size[0], screen.size[1], x_divisions, y_divisions)
        player.organise_player_info()
        
    def update_card_coords(player, width, height, xd, yd):
        player.shrink_amount = (width + height) * 0.015
        player.topleft, player.topright, player.bottomleft, player.bottomright = get_card_coords(width, height, xd, yd, player.num)
        
        player.coords = (player.topleft.xy + (player.shrink_amount, player.shrink_amount),
                         player.topright.xy + (-player.shrink_amount, player.shrink_amount), 
                         player.bottomright.xy + (-player.shrink_amount, -player.shrink_amount), 
                         player.bottomleft.xy + (player.shrink_amount, -player.shrink_amount))

        player.organise_player_info()
        player.xy_pos_updated = False
        
    def draw_card_lines(player, screen, color):
        pg.draw.polygon(screen, player.color, player.coords)
    
        pg.draw.line(screen, color,
                     (player.topleft.x + player.shrink_amount, 
                      (player.topleft.y + (player.bottomleft.y - player.topleft.y) * 0.2 + player.shrink_amount)),
                     (player.topright.x - player.shrink_amount, 
                      (player.topright.y + (player.bottomright.y - player.topright.y) * 0.2) + player.shrink_amount), 
                     3)
        
        pg.draw.line(screen, color, ((player.topleft.x + (player.topright.x - player.topleft.x) * 1/3), 
                                       (player.topleft.y + (player.bottomleft.y - player.topleft.y) * 0.2 + player.shrink_amount)), 
                                      ((player.topleft.x + (player.topright.x - player.topleft.x) * 1/3), 
                                       player.bottomleft.y - player.shrink_amount), 
                                      3)
        
        pg.draw.line(screen, color, ((player.topleft.x + (player.topright.x - player.topleft.x) * 2/3), 
                                       (player.topleft.y + (player.bottomleft.y - player.topleft.y) * 0.2 + player.shrink_amount)), 
                                      ((player.topleft.x + (player.topright.x - player.topleft.x) * 2/3), 
                                       player.bottomleft.y - player.shrink_amount), 
                                      3)
        
        pg.draw.line(screen, color, ((player.topleft.x + (player.topright.x - player.topleft.x) * 1/3),
                                       ((player.topleft.y + ((player.bottomleft.y - player.topleft.y)) * 6/10))), 
                                      ((player.topleft.x + (player.topright.x - player.topleft.x) * 2/3), 
                                       ((player.topleft.y + ((player.bottomleft.y - player.topleft.y)) * 6/10))),
                                      3)
        
    def draw_card_info_txt(player, screen, inverted_color, is_timer_on, mouse_clicked, font_path, mouse_pos):
        player.name_selected_this_frame = False

        for info in player.infos:
            info.hovered = Point(mouse_pos.x, mouse_pos.y).within(Polygon(info.coords))

            if info.is_text and info.hovered and mouse_clicked:
                info.selected = True
                player.is_changing_name = True
                player.name_selected_this_frame = True

            if info.is_text and (not info.hovered) and mouse_clicked:
                info.selected = False
                player.is_changing_name = False

            info.draw(screen, font_path, mouse_clicked, is_timer_on, inverted_color)

            if info.is_text:
                player.name_txt_rect = info.text_rect

    def organise_player_info(player):
        class PlayerInfo:
            def __init__(info, coords, value, is_button=False, is_text=False, group_key=None):
                info.coords = coords
                info.value = value
                info.is_button = is_button
                info.is_text = is_text
                info.group_key = group_key

                info.selected = False
                info.text_rect = None

                c = coords[0]
                info.true_x_pos = c[0]
                info.true_y_pos = c[1]
                info.x_pos = c[0]
                info.y_pos = c[1]

                info.hovered = False
                info._pos_centered_once = False
                info._pos_left_once = False
                
            def _polygon_bounds(info):
                xs = [p[0] for p in info.coords]
                ys = [p[1] for p in info.coords]
                return min(xs), min(ys), max(xs), max(ys)

            def _rect_w(info, r):
                if r is None:
                    return 0
                return r.width if hasattr(r, "width") else r[2]

            def _rect_h(info, r):
                if r is None:
                    return 0
                return r.height if hasattr(r, "height") else r[3]

            def center_text_pos_once(info):
                if info.text_rect is None or info._pos_centered_once:
                    return
                x1, y1, x2, y2 = info._polygon_bounds()
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                info.x_pos = cx - info._rect_w(info.text_rect) / 2
                info.y_pos = cy - info._rect_h(info.text_rect) / 2
                info._pos_centered_once = True

            def left_text_pos_once(info, padding):
                if info.text_rect is None or info._pos_left_once:
                    return
                x1, y1, x2, y2 = info._polygon_bounds()
                cy = (y1 + y2) / 2
                info.x_pos = x1 + padding
                info.y_pos = cy - info._rect_h(info.text_rect) / 2
                info._pos_left_once = True

            def _apply_group_exclusive(info):
                if info.group_key is None:
                    return
                for other in player.infos:
                    if other is info:
                        continue
                    if getattr(other, "group_key", None) == info.group_key:
                        other.selected = False

            def draw(info, screen, font_path, is_clicked, is_timer_on, inverted_color):
                color = inverted_color
                if info.is_text:
                    info.draw_txt(screen, is_clicked, is_timer_on, color, font_path)
                elif info.is_button:
                    info.draw_button(screen, is_clicked, color, font_path)

            def draw_button(info, screen, is_clicked, color, font_path):
                if info.selected:
                    pg.draw.polygon(screen, color, info.coords)
                    txt_color = player.color
                elif info.hovered:
                    txt_color = player.color
                    pg.draw.polygon(screen, color, info.coords)
                    if is_clicked:
                        info.selected = True
                        player.type = info.value
                        info._apply_group_exclusive()
                else:
                    txt_color = color

                info.text_rect = draw_text(
                    screen, font_path, player.shrink_amount,
                    info.value, txt_color, info.x_pos, info.y_pos,
                    get_rect=True
                )

                if not player.xy_pos_updated:
                    info.center_text_pos_once()

            def draw_txt(info, screen, is_clicked, is_timer_on, color, font_path):
                if info.selected and not (is_clicked and not info.hovered):
                    if is_timer_on and info.text_rect is not None:
                        pg.draw.line(
                            screen, color,
                            (info.text_rect[0] + info.text_rect[2] + 1, info.text_rect[1]),
                            (info.text_rect[0] + info.text_rect[2] + 1, info.text_rect[1] + info.text_rect[3])
                        )
                elif info.hovered:
                    if is_clicked:
                        info.selected = True
                else:
                    pg.draw.polygon(screen, color, info.coords)
                    color = player.color
                    info.selected = False

                info.text_rect = draw_text(
                    screen, font_path, player.shrink_amount,
                    info.value, color, info.x_pos, info.y_pos,
                    get_rect=True
                )


                if not player.xy_pos_updated:

                    info.left_text_pos_once(padding=player.shrink_amount * 0.6)

        name = PlayerInfo(
            (player.topleft.xy + (player.shrink_amount, player.shrink_amount),
             player.topright.xy + (-player.shrink_amount, player.shrink_amount),
             (player.topright.x - player.shrink_amount, (player.topright.y + (player.bottomright.y - player.topright.y) * 0.2) + player.shrink_amount),
             (player.topleft.x + player.shrink_amount, player.topleft.y + (player.bottomleft.y - player.topleft.y) * 0.2 + player.shrink_amount)),
            player.name,
            is_text=True
        )
        
        human = PlayerInfo(
            ((player.topleft.x + (player.topright.x - player.topleft.x) * 1/3,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 0.2 + player.shrink_amount),
             (player.topleft.x + (player.topright.x - player.topleft.x) * 1/3,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 6/10),
             (player.topleft.x + (player.topright.x - player.topleft.x) * 2/3,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 6/10),
             (player.topleft.x + (player.topright.x - player.topleft.x) * 2/3,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 0.2 + player.shrink_amount)),
            "human",
            is_button=True,
            group_key="player_type"
        )
        
        bot = PlayerInfo(
            ((player.topleft.x + (player.topright.x - player.topleft.x) * 1/3,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 6/10),
             (player.topleft.x + (player.topright.x - player.topleft.x) * 2/3,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 6/10),
             (player.topleft.x + (player.topright.x - player.topleft.x) * 2/3,
              player.bottomleft.y - player.shrink_amount),
             (player.topleft.x + (player.topright.x - player.topleft.x) * 1/3,
              player.bottomleft.y - player.shrink_amount)),
            "bot",
            is_button=True,
            group_key="player_type"
        )
        
        player.infos = [name, human, bot]
        player.name_info = name
        player.xy_pos_updated = False
        
    def draw_card(player, screen, is_timer_on, mouse_clicked, font_path, mouse_pos):
        inverted_player_color = [-color + 255 for color in player.color]
        
        player.draw_card_lines(screen, inverted_player_color)
        player.draw_card_info_txt(screen, inverted_player_color, is_timer_on, mouse_clicked, font_path, mouse_pos)
        player.draw_color_picker()

        if not player.xy_pos_updated:
            player.xy_pos_updated = True
        
    def draw_color_picker(player):
        surf_destination = pg.Vector2(player.topleft.x + player.shrink_amount * 1.5,
                                      player.topleft.y + (player.bottomleft.y - player.topleft.y) * 0.2 + player.shrink_amount * 1.5)
        
        player.surf_area = pg.Vector2((player.topright.x - player.topleft.x) * 1/3 - player.shrink_amount*2, 
                               player.bottomleft.y - ((player.topright.y + (player.bottomright.y - player.topright.y) * 0.2) + player.shrink_amount) - player.shrink_amount * 2)
        
        player.picked_color_surf = (int(surf_destination.x),
                                   int(surf_destination.y), 
                                   int(player.surf_area.x),
                                   int(player.surf_area.y))
        
        if player.draw_button_once_flag:
            if player.kill_button:
                if hasattr(player, "colour_picker_button"):
                    player.colour_picker_button.kill()
                player.kill_button = False
 
            player.colour_picker_button = UIButton(
                relative_rect=pg.Rect(player.picked_color_surf),
                text='Pick Colour',
                manager=player.ui_manager
            )
            player.draw_button_once_flag = False


def get_card_coords(width, height, xd, yd, num):
    topleft = pg.Vector2(((num%yd)%100)/yd*width, (int(num/yd))/xd*height)
    topright = pg.Vector2((((num%yd)+1)%100)/yd*width, (int(num/yd))/xd*height)
    bottomleft = pg.Vector2(((num%yd)%100)/yd*width, (int(num/yd)+1)/xd*height)
    bottomright = pg.Vector2((((num%yd)+1)%100)/yd*width, (int(num/yd)+1)/xd*height)
    return topleft, topright, bottomleft, bottomright
        

class Game:
    def __init__(self, clock: pg.time.Clock, bot_versions: list, screen: object) -> None:
        self.clock = clock
        self.bot_versions = bot_versions
        
        self.screen = screen
        self.font_path = "font/EraserRegular.ttf"
        
        self.width = screen.size[0]
        self.height = screen.size[1]
        
        self.playing = True
        self.scroll = 0
        self.settings_selected = False
        self.ui_manager = pygame_gui.UIManager((self.width, self.height))
        
        self.event_1 = pg.USEREVENT + 100
        pg.time.set_timer(self.event_1, 500)
        self.is_timer_on = False
        
        self.manage_cards = ManageCards(screen, self.ui_manager)

        self.mouse_clicked = False

    def init_game(self):
        players = self.manage_cards.players
        print(players)
        self.countries = MakeCountries(players).countries
        self.manage_players = PlayerManager(screen, players, self.countries, self.bot_versions, self.font_path)
        self.draw = Draw(screen, self.countries, self.font_path) 
        
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
                    country.check_hovered(mouse_pos, self.draw.mouse_offset, self.mouse_clicked)
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
