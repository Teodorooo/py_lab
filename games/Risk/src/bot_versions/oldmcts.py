from copy import deepcopy
from random import randint, choice
from math import sqrt, log
from src.utils import Utils

attack_calculation = Utils().attack_calculation 

class GameState:
    def __init__(self, players, current_player_index, countries, starting_phase, phase, fortified, conquered_country):
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
    
    def get_valid_actions(self, state) -> set:
        actions = []

        phase = state["phase"]
        player = self.get_active_player_name(state)
        countries = state["countries"]
        available_units = state["players"][player]["available_units"]
        starting_phase = state["starting_phase"]
        fortified = state["fortified"]
        conquered_country = state['conquered_country']
        actions = set()

        controlled = [name for name, info in countries.items() if info["owner"] == player]
        
        if conquered_country:
            actions = set(("conquered_country", 
                             conquered_country['from'], 
                             conquered_country['to'], 
                             u) 
                            for u in range(1, (countries[conquered_country['from']]['units'] - 1) + 1))
        
        elif phase == "place":
            if starting_phase:
                actions = set(("place", country, 1) 
                           for country in controlled)

            elif available_units > 0:
                actions = set(("place", country, units) 
                           for units in range(1, available_units + 1, 1) for country in controlled)
                actions.add(("skip_to_attack",))
            else:
                actions.add(("skip_to_attack",))
                
        elif phase == "attack":
            for country in controlled:
                if state['countries'][country]["units"] > 1:
                    for neighbor in state['countries'][country]["neighbours"]:
                        if countries[neighbor]["owner"] != player:
                            max_attack = min(state['countries'][country]["units"] - 1, 3)
                            for u in range(1, max_attack + 1):
                                actions.add(( 
                                    "attack",
                                    country,
                                    neighbor,
                                    u,
                                ))
            actions.add(("skip_to_fortify",))
                                    
        elif phase == "fortify":
            if not fortified:
                for src in controlled:
                    src_info = countries[src]
                    if src_info["units"] > 1:
                        neighbors = self.get_all_neighbours(countries, src, player)
                        for dst in neighbors:
                            for u in range(1, src_info["units"]):
                                actions.add((
                                    "fortify",
                                    src,
                                    dst,
                                    u,
                                ))
            actions.add(("end_turn",))
            
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
        
        action_type = action[0]
        
        available_units = state['players'][player]['available_units']
        countries = state["countries"]
        conquered_country = state['conquered_country']
        fortified = state['fortified']
        
        if conquered_country:
            for country in countries:
                if country == conquered_country['from']:
                    new_state['countries'][country]['units'] -= action[-1] # action["units"]
                if country == conquered_country['to']:
                    new_state['countries'][country]['units'] += action[-1] # units
                new_state['conquered_country'] = None
                
        elif action_type == "place":
            for country in countries:
                if country == action[1]:  # action["country"]           
                    new_state['players'][player]['available_units'] -= action[-1] # units              
                    new_state['countries'][country]['units'] += action[-1] # units              
                    if available_units <= 0:                   
                        new_state['starting_phase'] = False   
                    if new_state['starting_phase']:
                        new_state['phase'] = 'place'                  
                        
        elif action_type == "attack":                 
            for country in countries:                   
                if action[2] == country: # if defender == country:                   
                    defender = country                   
                if action[1] == country: # if attacker == country:                  
                    attacker = country                   
                    
            new_state['countries'][defender]['units'], new_state['countries'][attacker]['units'] = attack_calculation(                   
                action[-1], # units                    
                new_state['countries'][defender]['units'],                    
                new_state['countries'][attacker]['units']                                                 
            )                                      
            if new_state['countries'][defender]['units'] <= 0:                              
                new_state['conquered_country'] = {'from': attacker, 'to': defender}                              
                new_state['countries'][defender]['owner'] = player                              

        elif action_type == "fortify":                              
            if not fortified:                              
                for country in countries:                              
                    if country == action[1]: # unit granting country                            
                        new_state['countries'][country]['units'] -= action[-1] # units                            
                    if country == action[2]: # unit receiving country                             
                        new_state['countries'][country]['units'] += action[-1] # units                        
                    new_state['fortified'] = True                              
    
        else: # skip phase                              
            if action == 'skip_to_attack':                                                           
                new_state['phase'] = 'attack'                              
    
            elif action == 'skip_to_fortify':                              
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
        player = self.get_active_player_name(state)
        owners = {c['owner'] for c in state['countries'].values()}

        if len(owners) == 1 and player in owners:
            return 1 # win
        elif player not in owners:
            return -1 # loss
        else:
            return 0 # game not finished
        
class Node:
    def __init__(node, action, state, parent, player_index):
        node.action = action
        node.state = state
        node.parent = parent
        node.children = []
        node.untried = set()
        node.tried = set()
        node.visits = 0
        node.value_sum = 0
        node.player_index = player_index
            
class OldMCTS:
    def __init__(self, players, countries, starting_phase, root_player_index, phase, fortified, conquered_country, n_iterations=200, depth=8, exploration_constant=sqrt(2)):
        self.players = players
        self.countries = countries
        self.root_player_index = root_player_index
        self.n_iterations = n_iterations
        self.depth = depth
        self.exploration_constant = exploration_constant
        
        self.game_state = GameState(self.players, 
                                    self.root_player_index,
                                    self.countries,
                                    starting_phase,
                                    phase,
                                    fortified,
                                    conquered_country
                                    )
        
        self.root_state = self.game_state.root_state
        
        self.root_node = Node(
            None,
            self.root_state,
            None,
            self.root_player_index
        )

        self.alpha = 1
        # print(self.heuristic_score(self.game_state.root_state))
        
    def expand(self, parent):
        if not parent.untried:
            parent.untried = self.game_state.get_valid_actions(parent.state)
            
        parent.untried.difference_update(parent.tried)
        
        if not parent.untried:
            return parent

        actions = parent.untried
        best_action = {"action": None, "score": float('-inf')}

        for _ in range(min(100, len(actions))):
            random_action = list(actions)[randint(0, len(actions) - 1)]
            actions.remove(random_action)
            
            state = self.game_state.apply_action(parent.state, random_action)
            score = self.heuristic_score(state)
            
            if score > best_action['score']:
                best_action['action'] = random_action
                best_action['score'] = score
            
        action = best_action['action'] 

        parent.tried.add(action)
        
        new_node = Node(action,
                        self.game_state.apply_action(parent.state, action),
                        parent,
                        (parent.player_index+1)%len(self.players))
        
        parent.children.append(new_node)
        
        return new_node

    def best_child(self, node):
        best = None
        best_score = float("-inf")
        C = self.exploration_constant
        unvisited_children = {"child": None, "score": float("-inf")}

        for child in node.children:
            if child.visits == 0:
                score = self.heuristic_score(child.state)
                if score > unvisited_children['score']:
                    unvisited_children['child'] = child
                    unvisited_children['score'] = score
            else:

                Q = child.value_sum / child.visits
                N = node.visits
                n = child.visits
                U = C * sqrt(log(N) / n)

                H = self.heuristic_score(child.state)    
                
                score = Q + U + self.alpha * H
            if score > best_score:
                best_score = score
                best = child
            
        if unvisited_children['child']:
            best = unvisited_children['child']
        
        return best

    def heuristic_score(self, state):
        countries = state['countries']
        players = state['players']
        active_player = None
        unused_units = 0
        units_in_board = 0
        
        for player in players:
            if players[player]['player_index'] == state['current_player_index']:
                active_player = player
                break
        
        for country in countries:
            if countries[country]['owner'] == active_player:
                is_safe = True
                units_in_board += countries[country]['units'] - 1
                for neighbour in countries[country]["neighbours"]:
                    if countries[neighbour]["owner"] != active_player:
                        is_safe = False
                        break
                if is_safe:
                    unused_units += countries[country]["units"] - 1

        try:
            unused_percentage = unused_units / units_in_board
        except ZeroDivisionError:
            unused_percentage = -0.5
        
        A = -155/9
        B = 167/6
        C = -227/18
        D = 1.0
        
        score = A*unused_percentage**3 + B*unused_percentage**2 + C*unused_percentage + D

        return score
     
    def selection(self, node):
        current_child = node
        for _ in range(self.depth):
            if self.game_state.is_terminal(current_child.state):
                return current_child
            elif current_child.untried or not current_child.children:
                return current_child
            
            current_child = self.best_child(current_child)
        else:
            return current_child
        
    def simulate(self, node):
        state = node.state
        for _ in range(self.depth):
            terminal_val = self.game_state.is_terminal(state)
            if terminal_val != 0: # if the game is finished
                return terminal_val
            
            actions = list(self.game_state.get_valid_actions(state))
            
            if not actions:
                break
            
            state = self.game_state.apply_action(state, choice(actions))
               
        return max(-1, min(1, self.alpha * self.heuristic_score(state)))
    
    def backpropagate(self, node, reward):
        cur = node
        while cur is not None:
            cur.visits += 1
            cur.value_sum += reward
            cur = cur.parent
            
    def get_action(self):
        self.root_node.untried = self.game_state.get_valid_actions(self.root_node.state)
        if not self.root_node.untried:
            return "no available actions"
            
        for _ in range(self.n_iterations):
            node = self.selection(self.root_node)
            if node.untried:
                node = self.expand(node)
            node_reward = self.simulate(node)
            self.backpropagate(node, node_reward)
        
        if not self.root_node.children:
            return "no children in root node"
        
        best_child = self.root_node.children[0]
        for child in self.root_node.children:
            if child.visits > best_child.visits:
                best_child = child
                
        best_action = best_child.action
        
        return best_action
    
