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

class OldMCTS:
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