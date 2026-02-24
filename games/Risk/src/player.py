from random import shuffle
from src.utils import Utils
utils = Utils()
attack_calculation = utils.attack_calculation
draw_text = utils.draw_text

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

        current_player = self.player_objects[self.turn - 1]
        
        finished_starting_phase = []
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
            current_player.bot_play(self.starting_phase)
        
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
        
        super().update_controlled_countries()
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
    def __init__(self, screen, countries, player_name, players, font, bot_version, mcts):
        super().__init__(screen, countries, player_name, players, font)
        
        self.player_index = self.players[player_name]['playing_order']
        self.conquered_country = None
        self.bot_version = bot_version
        self.mcts = mcts
        
    def bot_play(self, starting_phase):
        self.end_turn = False
        self.starting_phase = starting_phase

        if self.phase == "place" and not self.new_army_received:
            self.update_army()  # add units if it's a new turn

        super().update_controlled_countries()
        
        self.mcts(self.players, self.countries, self.starting_phase, self.player_index, self.phase, self.fortified, self.conquered_country)
        mcts = self.mcts(self.players, self.countries, self.starting_phase, self.player_index, self.phase, self.fortified, self.conquered_country)
        
        action = mcts.get_action()
        
        action_type = action[0]

        if self.conquered_country:
            for country in self.countries:
                if country.name == action[1]:   # from country:
                    country.units -= action[-1] # - units
                if country.name == action[2]:   # to country:
                    country.units += action[-1] # + units
            self.conquered_country = None

        elif action_type == "place":
            for country in self.controlled_countries:
                if country.name == action[1]:         # place country
                    self.available_units -= action[2] # - units
                    country.units += action[2]        # + units
            if self.starting_phase:
                self.end_turn = True

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

        else: # skip_phase
            if action_type == "skip_to_attack":
                self.phase = "attack"
            elif action_type == "skip_to_fortify":
                self.phase = "fortify"
                self.fortified = False
            elif action_type == "e": 
                self.end_turn = True
                self.phase = "place"
                self.new_army_received = False
                
        super().update_controlled_countries()
        super().draw_player_and_phase()