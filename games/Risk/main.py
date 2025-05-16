import json 
import pygame as pg
import sys
import pandas as pd
from shapely.geometry import Point, Polygon
import random
from copy import deepcopy
import numpy as np
from math import sqrt

class PlayerManager:
    def __init__(self, players, countries):
        self.players = players
        self.countries = countries
        self.turn = 1

        self.add_starting_units()
        self.assign_playing_order()

        self.player_objects = []
        self.create_player_objects()

        self.starting_phase = True
    
    def create_player_objects(self):
        for player, player_info in self.players.items():
            if player_info['is_bot']:
                self.player_objects.append(BotPlayer(self.countries, player, self.players))
            else:
                self.player_objects.append(HumanPlayer(self.countries, player, self.players))
                
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
            current_player.bot_play(self.starting_phase)
        
        if current_player.end_turn:
            self.turn = (self.turn % len(self.player_objects)) + 1

    def add_starting_units(self) -> None:
        for player_info in self.players.values():
            player_info['available_units'] = 5 - (len(self.players) - 2) * 5 
    
    def assign_playing_order(self):
        player_keys = list(self.players.keys())
        random.shuffle(player_keys)

        for i, player_name in enumerate(player_keys):
            self.players[player_name]['playing_order'] = i + 1

    def check_player_wins(self, all_countries) -> object:
        for player in self.player_objects:
            if len(player.controlled_countries) == all_countries:
                return player
            else:
                return None

class Player:
    def __init__(self, countries, player_name, players):
        self.player_name = player_name
        self.players = players
        self.countries = countries
        self.phase = 'place'

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
                self.fortify_once_flag = True                                                        
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
        draw_text(screen, font, f"{self.player_name}'s turn", (0, 0, 0), 10, HEIGHT/2, rect_color=self.color)
        draw_text(screen, font, f"Army: {self.available_units}", (0, 0, 0), 10, HEIGHT/1.75, rect_color=self.color)
        draw_text(screen, font, f"Phase: {self.phase}", (255,255,255), 10, HEIGHT/1.5)
                         
class HumanPlayer(Player):
    def __init__(self, countries, player_name, players):
        super().__init__(countries, player_name, players)
        
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
        button_hovered = draw_text(screen, font, ' Next Phase ', (200, 200, 255), 25, 25, rect_color = (0, 100, 0), get_hovered = True)                                                        
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
        
        button_is_hovered = draw_text(screen, font, f'{self.attacker.name if self.attacker else '(attacker)'} attacks {self.defender.name if self.defender else '(defender)'} with {self.deployed_units} units, click to confirm.', (200, 200, 255), 10, HEIGHT - 50, rect_color = (0, 100, 0), get_hovered = True)    

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
            button_is_hovered = draw_text(screen, font, f'Send {self.deployed_units} units to {self.defender.name}, click to confirm', (200, 200, 255), 10, HEIGHT - 50, rect_color = (0, 100, 0), get_hovered = True)
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
                    
        button_is_hovered = draw_text(screen, font, f'Move {self.deployed_units} units from {self.country_a.name if self.country_a else '(Country A)'} to {self.country_b.name if self.country_b else '(Country B)'}, click to confirm', (200, 200, 255), 10, HEIGHT - 50, rect_color = (0, 100, 0), get_hovered = True)
        
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
                                          
class GameState:
    def __init__(self, players, current_player_index, phase, countries, starting_phase, fortified, conquered_country):
        all_countries = self.get_simplified_countries(countries)
        all_players = self.get_simplified_players(players)
        
        self.root_state = {
                           'players': all_players,
                           'current_player_index': current_player_index,
                           'phase': phase,
                           'countries': all_countries,
                           'starting_phase': starting_phase,
                           'fortified': fortified,
                           'conquered_country': conquered_country
                           }
        
    def get_active_player_name(self, state) -> str:
        for name, info in state['players'].items():
            if info['player_index'] == state['current_player_index']:
                return name
        
    def get_simplified_players(self, players) -> dict:
        simplified_players = {f'{player_name}': {
                                    'player_index': player_info['playing_order'], 
                                    'available_units': player_info['available_units']
                                                } 
                              for player_name, player_info in players.items()}
        
        return simplified_players

    def get_simplified_countries(self, countries) -> dict:
        simplified_countries = {
            country.name: 
                {'owner': country.owner, 
                 'units': country.units, 
                 'neighbours': [neighbour.name for neighbour in country.neighbours]} 
                for country in countries
                }
        
        return simplified_countries
    
    def get_valid_actions(self, state) -> list:
        actions = []

        phase = state["phase"]
        player = self.get_active_player_name(state)
        countries = state["countries"]
        available_units = state["players"][player]["available_units"]
        starting_phase = state["starting_phase"]
        fortified = state["fortified"]
        conquered_country = state['conquered_country']

        controlled = [name for name, info in countries.items() if info["owner"] == player]

        if conquered_country:
            actions = [{
                "type": 'conquered_country',
                "from": conquered_country['from'],
                "to": conquered_country['to'],
                "units": u
                        }
                for u in range(1, (countries[conquered_country['from']]['units'] - 1) + 1)]
        
        elif phase == "place":
            if available_units > 0:
                actions = [
                    {"type": "place", "country": name, "units": 1}
                    for name in controlled
                ]
            if not starting_phase:
                actions.append({"type": "skip", "to": "attack"})
                
        elif phase == "attack":
            for country in controlled:
                if state['countries'][country]["units"] > 1:
                    for neighbor in state['countries'][country]["neighbours"]:
                        if countries[neighbor]["owner"] != player:
                            max_attack = min(state['countries'][country]["units"] - 1, 3)
                            for u in range(1, max_attack + 1):
                                actions.append({
                                    "type": "attack",
                                    "attacker": country,
                                    "defender": neighbor,
                                    "units": u
                                })
            actions.append({"type": "skip", "to": "fortify"})
            
        elif phase == "fortify":
            if not fortified:
                for src in controlled:
                    src_info = countries[src]
                    if src_info["units"] > 1:
                        neighbors = self.get_all_neighbours(countries, src, player)
                        for dst in neighbors:
                            for u in range(1, src_info["units"]):
                                actions.append({
                                    "type": "fortify",
                                    "from": src,
                                    "to": dst,
                                    "units": u
                                })
            actions.append({"type": "skip", "to": "end_turn"})

        return actions
    
    def get_all_neighbours(self, countries, start_name, owner) -> list:
        visited = set()
        stack = [start_name]
        connected = set()

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            if current != start_name:
                connected.add(current)
            for neighbor in countries[current]["neighbours"]:
                if countries[neighbor]["owner"] == owner:
                    stack.append(neighbor)

        return list(connected)

    def apply_action(self, state, action) -> dict:
        new_state = deepcopy(state)
        
        player = self.get_active_player_name(state)
        
        action_type = action.get("type")
        
        available_units = state['players'][player]['available_units']
        countries = state["countries"]
        conquered_country = state['conquered_country']
        fortified = state['fortified']
        
        if conquered_country:
            for country in countries:
                if country == conquered_country['from']:
                    new_state['countries'][country]['units'] -= action['units']
                if country == conquered_country['to']:
                    new_state['countries'][country]['units'] += action['units']
                new_state['conquered_country'] = None
                
        elif action_type == "place":
            for country in countries:
                if country == action['country']:                   
                    new_state['players'][player]['available_units'] -= action['units']                   
                    new_state['countries'][country]['units'] += action['units']                   
                    if available_units <= 0:                   
                        new_state['starting_phase'] = False   
                    if new_state['starting_phase']:
                        new_state['phase'] = 'place'                  
                        
        elif action_type == "attack":                 
            for country in countries:                   
                if action['defender'] == country:                   
                    defender = country                   
                if action['attacker'] == country:                   
                    attacker = country                   
                    
            new_state['countries'][defender]['units'], new_state['countries'][attacker]['units'] = attack_calculation(                   
                action['units'],                    
                new_state['countries'][defender]['units'],                    
                new_state['countries'][attacker]['units']                                                 
            )                                      
            if new_state['countries'][defender]['units'] <= 0:                              
                new_state['conquered_country'] = {'from': attacker, 'to': defender}                              
                new_state['countries'][defender]['owner'] = player                              

        elif action_type == "fortify":                              
            if not fortified:                              
                for country in countries:                              
                    if country == action['from']:                              
                        new_state['countries'][country]['units'] -= action['units']                              
                    if country == action['to']:                              
                        new_state['countries'][country]['units'] += action['units']                              
                    new_state['fortified'] = True                              
    
        else: # skip phase                              
            if action['to'] == 'attack':                              
                if state['starting_phase']:                              
                    new_state['phase'] = 'attack'                              
    
            elif action['to'] == 'fortify':                              
                new_state['phase'] = 'fortify'                              
                new_state['fortified'] = False                              
    
            else: # end turn                              
                self.end_turn(new_state)                              
        
        return new_state                                     
    
    def end_turn(self, state):
        state['current_player_index'] = (state['current_player_index'] % len(state["players"])) + 1
        state['phase'] = 'place'
        
        next_player = self.get_active_player_name(state)
        new_army = self.calculate_new_army(state, next_player)
        state['players'][next_player]['available_units'] += new_army         

    def calculate_new_army(self, state, player) -> int:
        owned_countries = 0
        
        for country in state['countries']:
            if state['countries'][country]['owner'] == player:
                owned_countries += 1
                
        new_army = int(owned_countries / 3)
        
        return new_army if new_army > 3 else 3
    
    def is_terminal(self, state):
        player = self.get_active_player_name(self.root_state)
        owners = {c['owner'] for c in state['countries'].values()}

        if len(owners) == 1 and player in owners:
            return 'win'
        elif player not in owners:
            return 'lose'
        else:
            return None

class MCTS:
    def __init__(self, game_state_obj, n_iterations=1000, depth=30, exploration_constant=1.4):
        self.gs = game_state_obj
        self.n_iterations = n_iterations
        self.depth = depth
        self.exploration_constant = exploration_constant
        self.total_n = 0

        self.root_state = self.gs.root_state
        self.root_player = self.gs.get_active_player_name(self.root_state)

        self.tree = {
            (): {
                'state': self.root_state,
                'player': self.root_player,
                'parent': None,
                'children': {},
                'n': 0,
                'w': 0,
                'untried': self.gs.get_valid_actions(self.root_state),
            }
        }

    def select(self):
        node_id = ()
        while True:
            node = self.tree[node_id]

            if node['untried']:
                print(f"Selected expandable node: {node_id}")
                break
            if not node['children']:
                print(f"Selected leaf node (no children): {node_id}")
                break

            max_uct = -float('inf')
            best_action = None
            for action, child_id in node['children'].items():
                child = self.tree[child_id]
                n = child['n'] or 1e-6
                w = child['w']
                q = w / n
                uct = q + self.exploration_constant * np.sqrt(np.log(node['n'] + 1) / n)
                if uct > max_uct:
                    max_uct = uct
                    best_action = action

            print(f"UCT selection: {dict(best_action)} with UCT={max_uct:.3f}")
            node_id = node['children'][best_action]

        return node_id

    def expand(self, node_id):
        node = self.tree[node_id]
        if not node['untried']:
            return node_id

        action = node['untried'].pop()
        new_state = self.gs.apply_action(node['state'], action)
        child_id = node_id + (self._action_to_key(action),)
        self.tree[child_id] = {
            'state': new_state,
            'player': self.gs.get_active_player_name(new_state),
            'parent': node_id,
            'children': {},
            'n': 0,
            'w': 0,
            'untried': self.gs.get_valid_actions(new_state),
        }
        action_key = self._action_to_key(action)
        node['children'][action_key] = child_id
        print(f"Expanded action: {dict(action_key)} at node {child_id}")
        return child_id

    def simulate(self, node_id):
        state = deepcopy(self.tree[node_id]['state'])
        last_action = None

        for i in range(self.depth):
            if self.gs.is_terminal(state) in ("win", "lose"):
                break

            actions = self.gs.get_valid_actions(state)
            if not actions:
                break

            non_skip = [a for a in actions if a.get("type") != "skip"]
            action = random.choice(non_skip) if non_skip else random.choice(actions)
            state = self.gs.apply_action(state, action)
            last_action = action

        # Heuristic reward computation
        player = self.gs.get_active_player_name(state)
        all_countries = list(state['countries'].values())
        owned = [c for c in all_countries if c['owner'] == player]

        territory_ratio = len(owned) / len(all_countries)
        unit_score = sum(c['units'] for c in owned) / 100.0  # scale down

        attack_bonus = 0.5 if last_action and last_action.get("type") == "attack" else 0.0
        conquer_bonus = 1.0 if "conquered_country" in state else 0.0
        skip_penalty = 1.0 if last_action and last_action.get("type") == "skip" else 0.0

        # Total reward with exponential decay
        reward = territory_ratio + unit_score + attack_bonus + conquer_bonus - skip_penalty
        reward *= (0.99 ** i)

        print(f"Simulated reward: {reward:.3f} | action: {last_action}")
        return reward


    def backpropagate(self, node_id, result):
        if result == "win":
            reward = 1.0
        elif result == "lose":
            reward = -1.0
        else:
            reward = result

        path = []
        while node_id in self.tree:
            node = self.tree[node_id]
            path.append(node_id)
            node['n'] += 1
            if node['player'] == self.root_player:
                node['w'] += reward
            parent_id = node['parent']
            if parent_id is None:
                break
            node_id = parent_id

        print(f"Backprop path: {path[::-1]} | reward: {reward:.3f}")

    def solve(self):
        print("=== MCTS Starting ===")
        for i in range(self.n_iterations):
            print(f"\nIteration {i + 1}")
            self.total_n += 1
            node_id = self.select()
            child_id = self.expand(node_id)
            result = self.simulate(child_id)
            self.backpropagate(child_id, result)

        root_node = self.tree[()]
        best_action = None
        best_score = -float('inf')
        print("\n=== MCTS Final Evaluation ===")
        for action_key, child_id in root_node['children'].items():
            child = self.tree[child_id]
            q = child['w'] / (child['n'] or 1e-6)

            # Slightly discourage skip actions in final selection
            if dict(action_key).get("type") == "skip":
                q -= 0.1

            print(f"Action: {dict(action_key)} | Q = {q:.3f} | Visits = {child['n']}")
            if q > best_score:
                best_score = q
                best_action = action_key

        print(f"\nSelected Best Action: {dict(best_action)} with Q = {best_score:.3f}")
        return best_action, best_score, self.depth

    def _action_to_key(self, action):
        return tuple(sorted(action.items()))
          
class BotPlayer(Player):
    def __init__(self, countries, player_name, players):
        super().__init__(countries, player_name, players)
        
        self.player_index = self.players[player_name]['playing_order']
        self.conquered_country = None
        
    def bot_play(self, starting_phase):
        self.end_turn = False
        self.starting_phase = starting_phase

        if self.phase == "place" and not self.new_army_received:
            self.update_army()  # add units if it's a new turn

        self.update_controlled_countries()

        game_state = self.get_current_game_state()
        mcts = MCTS(game_state, n_iterations=200, depth=20, exploration_constant=sqrt(2))

        action, _, _ = mcts.solve()
        action = dict(action)
        action_type = action.get("type")

        if self.conquered_country:
            for country in self.countries:
                if country.name == action['from']:
                    country.units -= action['units']
                if country.name == action['to']:
                    country.units += action['units']
            self.conquered_country = None
            self.phase = "attack"

        elif action_type == "place":
            for country in self.controlled_countries:
                if country.name == action["country"]:
                    self.available_units -= action["units"]
                    country.units += action["units"]
            if self.starting_phase:
                self.end_turn = True
            elif self.available_units <= 0:
                self.phase = "attack"

        elif action_type == "attack":
            attacker = None
            defender = None
            for country in self.countries:
                if country.name == action["attacker"]:
                    attacker = country
                if country.name == action["defender"]:
                    defender = country

            if attacker and defender:
                defender.units, attacker.units = attack_calculation(
                    action["units"], defender.units, attacker.units
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
                    if country.name == action["from"]:
                        country.units -= action["units"]
                    if country.name == action["to"]:
                        country.units += action["units"]
                self.fortified = True
                self.end_turn = True  # done for this turn

        elif action_type == "skip":
            if action["to"] == "attack":
                self.phase = "attack"
            elif action["to"] == "fortify":
                self.phase = "fortify"
                self.fortified = False
            elif action["to"] == "end_turn":
                self.end_turn = True
                self.phase = "place"
                self.new_army_received = False  # allow next round to trigger `update_army`

        self.update_controlled_countries()
        super().draw_player_and_phase()

    def get_current_game_state(self):
        return GameState(
            self.players,
            self.player_index,
            self.phase, self.countries,
            self.starting_phase,
            self.fortified,
            self.conquered_country
        )

class Draw:
    def __init__(self, countries):
        self.countries = countries
        
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
                screen,
                country.color,
                [(x - self.mouse_offset.x, y - self.mouse_offset.y) for x, y in country.coords],
            )
            pg.draw.polygon(
                screen,
                (255, 255, 255),
                [(x - self.mouse_offset.x, y - self.mouse_offset.y) for x, y in country.coords],
                width=1,
            )
    
    def draw_units(self):
        for country in self.countries:
            draw_text(screen, small_font, str(country.units), (0, 0, 0), country.center.x - self.mouse_offset.x, country.center.y - self.mouse_offset.y, center = True)
            
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
        random.shuffle(all_starting_countries)      
        num = 0
        
        for player_info in self.players.values():
            player_info["controlled_countries"] = all_starting_countries[
                int(num) : int(len(all_starting_countries) / len(self.players) + num)]
            num += len(all_starting_countries) / len(self.players) 
        
    def read_geo_data(self) -> None:
        with open("./data/country_coords.json", "r") as f:
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
            "Estonia": ["Finland"]
        }
        name_to_country = {c.name: c for c in self.countries}
        
        if country.name in overrides:
            for neighbor_name in overrides[country.name]:
                if neighbor_name in name_to_country:
                    country.neighbours.append(name_to_country[neighbor_name])
        
class Game:
    def __init__(self, clock: pg.time.Clock):
        self.clock = clock
        self.playing = True
        self.scroll = 0
        
        self.players = {"player1": {"is_bot": True, "color": (0, 0, 255)},     # Add players here
                        "player2": {"is_bot": True, "color": (0, 255, 0)}}     
        
        self.countries = MakeCountries(self.players).countries
        self.manage_players = PlayerManager(self.players, self.countries)
        self.draw = Draw(self.countries)
        
    def run(self) -> None:
        while self.playing:
            self.clock.tick(60)
            screen.fill((60, 60, 60))
            self.events()
            mouse_pos = pg.Vector2(pg.mouse.get_pos())
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
        screen.fill(winning_player.color)
        draw_text(screen, font, f'{winning_player.player_name} won !', (0, 0, 0), WIDTH/2, HEIGHT/2, center=True)
    
    def events(self) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.playing = False
            self.mouse_clicked = event.type == pg.MOUSEBUTTONDOWN
            if event.type == pg.MOUSEWHEEL:
                self.scroll = event.dict['y']
                
def draw_text(screen: pg.Surface, font: pg.font.Font, text: str, color: tuple, x: int, y: int, center: bool = False, rect_color: tuple = None, get_hovered: bool = False) -> None:
    text_surf = font.render(text, False, color)
    text_rect = text_surf.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    if rect_color:
        pg.draw.rect(screen, rect_color, text_rect)
    screen.blit(text_surf, text_rect)
    
    if get_hovered and text_rect.collidepoint(pg.mouse.get_pos()):
        is_hovered = text_rect.collidepoint(pg.mouse.get_pos())
        return is_hovered

def attack_calculation(deployed_units, defender_units, attacker_units) -> int:
    attacker_rolls = sorted([random.randint(1, 6) for _ in range(deployed_units)], reverse=True)
    defender_rolls = sorted([random.randint(1, 6) for _ in range(min(2, defender_units))], reverse=True)
    
    for attack_roll, defense_roll in zip(attacker_rolls, defender_rolls):
        if attack_roll > defense_roll:
            defender_units -= 1
        else:
            attacker_units -= 1
      
    return defender_units, attacker_units 
     
pg.init()
pg.mixer.init()
pg.font.init()
pg.event.set_grab(True)

WIDTH = 1280
HEIGHT = 720
window_size = pg.Vector2(WIDTH, HEIGHT)

screen = pg.display.set_mode(window_size)
clock = pg.time.Clock()

font = pg.font.Font('font/EraserRegular.ttf', 30)
small_font = pg.font.Font('font/EraserRegular.ttf', 20)

pg.display.set_caption("Risk")

game = Game(clock)

game.run()

pg.quit()
sys.exit()