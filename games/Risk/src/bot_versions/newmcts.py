from random import choice, random, shuffle
from math import sqrt, log, ceil
from src.utils import Utils
from src.country import CONTINENT_COUNTRIES, CONTINENT_BONUSES

attack_calculation = Utils().attack_calculation

# ---------------------------------------------------------------------------
# Pre-built continent lookup: country_name -> continent_name
# ---------------------------------------------------------------------------
_COUNTRY_TO_CONTINENT = {}
for _cont, _members in CONTINENT_COUNTRIES.items():
    if _members is not None:
        for _c in _members:
            _COUNTRY_TO_CONTINENT[_c] = _cont


def _shallow_copy_state(state):
    """Efficient shallow copy that only copies mutable dicts, not nested structures"""
    return {
        'players': {name: dict(info) for name, info in state['players'].items()},
        'countries': {name: dict(info) for name, info in state['countries'].items()},
        'current_player_index': state['current_player_index'],
        'phase': state['phase'],
        'starting_phase': state['starting_phase'],
        'fortified': state['fortified'],
        'conquered_country': state['conquered_country'].copy() if state['conquered_country'] else None
    }


# ===================================================================
# GameState — manages state transitions and action generation
# ===================================================================
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def get_active_player_name(self, state) -> str:
        for name, info in state['players'].items():
            if info['player_index'] == state['current_player_index']:
                return name

    def get_simplified_players(self, players) -> dict:
        return {
            player_name: {
                'player_index': player_info['playing_order'],
                'available_units': player_info['available_units']
            }
            for player_name, player_info in players.items()
        }

    def get_simplified_countries(self, countries) -> dict:
        return {
            country.name: {
                'owner': country.owner,
                'units': country.units,
                'neighbours': [neighbour.name for neighbour in country.neighbours]
            }
            for country in countries
        }

    # ------------------------------------------------------------------
    # Border / strategic helpers (used by get_valid_actions & rollout)
    # ------------------------------------------------------------------
    def _get_border_territories(self, state, player):
        """Return list of country names owned by *player* that have at least one enemy neighbour."""
        countries = state['countries']
        borders = []
        for name, info in countries.items():
            if info['owner'] != player:
                continue
            for nb in info['neighbours']:
                if countries[nb]['owner'] != player:
                    borders.append(name)
                    break
        return borders

    def _enemy_pressure(self, state, country_name):
        """Sum of enemy units adjacent to *country_name*."""
        countries = state['countries']
        owner = countries[country_name]['owner']
        pressure = 0
        for nb in countries[country_name]['neighbours']:
            if countries[nb]['owner'] != owner:
                pressure += countries[nb]['units']
        return pressure

    # ------------------------------------------------------------------
    # Action generation  (REDUCED action space)
    # ------------------------------------------------------------------
    def get_valid_actions(self, state) -> set:
        phase = state['phase']
        player = self.get_active_player_name(state)
        countries = state['countries']
        available_units = state['players'][player]['available_units']
        starting_phase = state['starting_phase']
        fortified = state['fortified']
        conquered_country = state['conquered_country']

        actions = set()

        # --- conquered country: move troops in ---
        if conquered_country:
            max_movable = countries[conquered_country['from']]['units'] - 1
            if max_movable >= 1:
                actions.add(("conquered_country",
                             conquered_country['from'],
                             conquered_country['to'],
                             max_movable))
                half = max(1, max_movable // 2)
                if half != max_movable:
                    actions.add(("conquered_country",
                                 conquered_country['from'],
                                 conquered_country['to'],
                                 half))
            return actions

        # --- PLACE phase ---
        if phase == 'place':
            if available_units <= 0:
                actions.add(("skip_to_attack",))
                return actions

            if starting_phase:
                # Place 1 unit on a border territory (or any owned if no borders yet)
                borders = self._get_border_territories(state, player)
                targets = borders if borders else [n for n, i in countries.items() if i['owner'] == player]
                for t in targets:
                    actions.add(("place", t, 1))
                return actions

            # Non-starting: place ALL units on one border territory
            borders = self._get_border_territories(state, player)
            if not borders:
                borders = [n for n, i in countries.items() if i['owner'] == player]

            # Score borders by enemy pressure, pick top 10
            scored = sorted(borders, key=lambda b: self._enemy_pressure(state, b), reverse=True)
            top = scored[:10]

            for t in top:
                actions.add(("place", t, available_units))

            # "spread" option: distribute evenly among top-3 threatened borders
            # We represent this as placing on the single most threatened (the bot
            # will revisit placement each call anyway, and the game only places once
            # per call in the real game loop).  The top-10 already covers variety.

            actions.add(("skip_to_attack",))
            return actions

        # --- ATTACK phase ---
        if phase == 'attack':
            controlled = [n for n, i in countries.items() if i['owner'] == player]
            for country in controlled:
                units = countries[country]['units']
                if units < 4:  # need at least 4 to attack with 3 dice (units-1 >= 3)
                    continue
                max_dice = min(units - 1, 3)
                for nb in countries[country]['neighbours']:
                    if countries[nb]['owner'] != player:
                        actions.add(("attack", country, nb, max_dice))

            actions.add(("skip_to_fortify",))
            return actions

        # --- FORTIFY phase ---
        if phase == 'fortify':
            if not fortified:
                controlled = [n for n, i in countries.items() if i['owner'] == player]
                borders_set = set(self._get_border_territories(state, player))

                count = 0
                for src in controlled:
                    if countries[src]['units'] <= 1:
                        continue
                    reachable = self.get_all_neighbours(countries, src, player)
                    # Only fortify TO border territories
                    border_dsts = [d for d in reachable if d in borders_set]
                    for dst in border_dsts:
                        max_move = countries[src]['units'] - 1
                        half_move = max(1, max_move // 2)
                        actions.add(("fortify", src, dst, max_move))
                        if half_move != max_move:
                            actions.add(("fortify", src, dst, half_move))
                        count += 1
                        if count >= 15:
                            break
                    if count >= 15:
                        break

            actions.add(("end_turn",))
            return actions

        return actions

    # ------------------------------------------------------------------
    # Reachability for fortify
    # ------------------------------------------------------------------
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
            for neighbor in countries[current]['neighbours']:
                if countries[neighbor]['owner'] == owner:
                    stack.append(neighbor)
        return list(connected)

    # ------------------------------------------------------------------
    # Apply action  (same logic as before, with fixes kept)
    # ------------------------------------------------------------------
    def apply_action(self, state, action) -> dict:
        new_state = _shallow_copy_state(state)
        player = self.get_active_player_name(state)
        action_type = action[0]
        conquered_country = state['conquered_country']

        if conquered_country:
            from_c = conquered_country['from']
            to_c = conquered_country['to']
            new_state['countries'][from_c]['units'] -= action[-1]
            new_state['countries'][to_c]['units'] += action[-1]
            new_state['conquered_country'] = None

        elif action_type == 'place':
            country = action[1]
            units = action[-1]
            new_state['players'][player]['available_units'] -= units
            new_state['countries'][country]['units'] += units
            if new_state['players'][player]['available_units'] <= 0:
                new_state['starting_phase'] = False
            if new_state['starting_phase']:
                new_state['phase'] = 'place'

        elif action_type == 'attack':
            attacker = action[1]
            defender = action[2]
            new_state['countries'][defender]['units'], new_state['countries'][attacker]['units'] = attack_calculation(
                action[-1],
                new_state['countries'][defender]['units'],
                new_state['countries'][attacker]['units']
            )
            if new_state['countries'][defender]['units'] <= 0:
                new_state['countries'][defender]['units'] = 0
                new_state['conquered_country'] = {'from': attacker, 'to': defender}
                new_state['countries'][defender]['owner'] = player

        elif action_type == 'fortify':
            src = action[1]
            dst = action[2]
            units = action[-1]
            if not state['fortified']:
                new_state['countries'][src]['units'] -= units
                new_state['countries'][dst]['units'] += units
                new_state['fortified'] = True

        else:  # skip / end
            if action_type == 'skip_to_attack':
                new_state['phase'] = 'attack'
            elif action_type == 'skip_to_fortify':
                new_state['phase'] = 'fortify'
                new_state['fortified'] = False
            else:  # end_turn
                self.end_turn(new_state)

        return new_state

    # ------------------------------------------------------------------
    def end_turn(self, state):
        state['current_player_index'] = (state['current_player_index'] % len(state['players'])) + 1
        state['phase'] = 'place'
        next_player = self.get_active_player_name(state)
        new_army = self.calculate_new_army(state, next_player)
        state['players'][next_player]['available_units'] += new_army

    def calculate_new_army(self, state, player) -> int:
        countries = state['countries']
        owned_countries = sum(1 for c in countries.values() if c['owner'] == player)
        base = max(3, int(owned_countries / 3))

        # Continent bonuses
        continent_counts = {}
        continent_totals = {}
        for name, info in countries.items():
            cont = _COUNTRY_TO_CONTINENT.get(name)
            if cont is None:
                continue
            continent_totals[cont] = continent_totals.get(cont, 0) + 1
            if info['owner'] == player:
                continent_counts[cont] = continent_counts.get(cont, 0) + 1

        bonus = 0
        for cont, total in continent_totals.items():
            if continent_counts.get(cont, 0) == total:
                bonus += CONTINENT_BONUSES.get(cont, 0)

        return base + bonus

    def is_terminal(self, state):
        owners = {c['owner'] for c in state['countries'].values()}
        return len(owners) == 1


# ===================================================================
# Node
# ===================================================================
class Node:
    __slots__ = ('action', 'state', 'parent', 'children', 'untried',
                 'tried', 'visits', 'value_sum', 'player_index')

    def __init__(self, action, state, parent, player_index):
        self.action = action
        self.state = state
        self.parent = parent
        self.children = []
        self.untried = set()
        self.tried = set()
        self.visits = 0
        self.value_sum = 0
        self.player_index = player_index


# ===================================================================
# NewMCTS — dramatically improved MCTS agent
# ===================================================================
class NewMCTS:
    def __init__(self, players, countries, starting_phase, root_player_index, phase, fortified, conquered_country,
                 n_iterations=500, depth=12, exploration_constant=sqrt(2)):
        self.players = players
        self.countries = countries
        self.root_player_index = root_player_index
        self.n_iterations = n_iterations
        self.depth = depth
        self.exploration_constant = exploration_constant

        self.game_state = GameState(
            self.players,
            self.root_player_index,
            self.countries,
            starting_phase,
            phase,
            fortified,
            conquered_country
        )

        self.root_state = self.game_state.root_state
        self.root_player = self.game_state.get_active_player_name(self.root_state)

        self.root_node = Node(
            None,
            self.root_state,
            None,
            self.root_player_index
        )

    # ------------------------------------------------------------------
    # Multi-factor evaluation  [-1, 1]
    # ------------------------------------------------------------------
    def evaluate(self, state):
        """Evaluate state from the ROOT player's perspective."""
        player = self.root_player
        countries = state['countries']
        total = len(countries)
        owned = 0
        total_my_units = 0
        border_my_units = 0
        border_diff_sum = 0
        border_count = 0

        # Continent tracking
        continent_owned = {}
        continent_total = {}

        for name, info in countries.items():
            cont = _COUNTRY_TO_CONTINENT.get(name)
            if cont is not None:
                continent_total[cont] = continent_total.get(cont, 0) + 1

            if info['owner'] == player:
                owned += 1
                total_my_units += info['units']
                is_border = False
                for nb in info['neighbours']:
                    if countries[nb]['owner'] != player:
                        is_border = True
                        border_diff_sum += info['units'] - countries[nb]['units']
                        border_count += 1
                if is_border:
                    border_my_units += info['units']

                if cont is not None:
                    continent_owned[cont] = continent_owned.get(cont, 0) + 1

        # Terminal
        if owned == total:
            return 1.0
        if owned == 0:
            return -1.0

        # 1. Territory ratio  (weight 0.35)
        territory_score = (owned / total) * 2 - 1  # maps [0,1] -> [-1,1]

        # 2. Continent proximity  (weight 0.25)
        max_continent_value = sum(CONTINENT_BONUSES.values())
        continent_score_raw = 0.0
        for cont, ct in continent_total.items():
            co = continent_owned.get(cont, 0)
            bonus = CONTINENT_BONUSES.get(cont, 0)
            ratio = co / ct if ct > 0 else 0
            continent_score_raw += (ratio ** 2) * bonus
        # Normalize to [0, 1] then shift to [-1, 1]
        continent_score = (continent_score_raw / max_continent_value) * 2 - 1 if max_continent_value > 0 else 0

        # 3. Border strength  (weight 0.25)
        if border_count > 0:
            avg_diff = border_diff_sum / border_count
            # Soft clamp to [-1, 1] using tanh-like sigmoid
            border_score = max(-1.0, min(1.0, avg_diff / 5.0))
        else:
            border_score = 0.5  # no borders = good (interior only)

        # 4. Army concentration  (weight 0.15)
        if total_my_units > 0:
            concentration = border_my_units / total_my_units
            concentration_score = concentration * 2 - 1  # [0,1] -> [-1,1]
        else:
            concentration_score = -1.0

        score = (0.35 * territory_score +
                 0.25 * continent_score +
                 0.25 * border_score +
                 0.15 * concentration_score)

        return max(-1.0, min(1.0, score))

    # ------------------------------------------------------------------
    # Progressive widening expand
    # ------------------------------------------------------------------
    def expand(self, parent):
        # Progressive widening: limit children to ceil(2 * sqrt(visits))
        max_children = max(1, ceil(2 * sqrt(max(1, parent.visits))))
        if len(parent.children) >= max_children:
            return self.best_child(parent)

        if not parent.untried:
            parent.untried = self.game_state.get_valid_actions(parent.state)
        parent.untried.difference_update(parent.tried)

        if not parent.untried:
            if parent.children:
                return self.best_child(parent)
            return parent

        # Pick the action with best immediate heuristic
        actions_list = list(parent.untried)
        # Evaluate a subset to keep expand fast
        sample_size = min(len(actions_list), 20)
        if sample_size < len(actions_list):
            shuffle(actions_list)
            actions_list = actions_list[:sample_size]

        best_action = None
        best_score = float('-inf')
        best_state = None

        for action in actions_list:
            st = self.game_state.apply_action(parent.state, action)
            sc = self.evaluate(st)
            if sc > best_score:
                best_score = sc
                best_action = action
                best_state = st

        parent.tried.add(best_action)

        new_node = Node(
            best_action,
            best_state,
            parent,
            best_state['current_player_index']
        )
        parent.children.append(new_node)
        return new_node

    # ------------------------------------------------------------------
    # UCB1 selection of best child
    # ------------------------------------------------------------------
    def best_child(self, node):
        best = None
        best_score = float('-inf')
        C = self.exploration_constant
        log_N = log(max(1, node.visits))

        for child in node.children:
            if child.visits == 0:
                # Unvisited children get priority with a heuristic tiebreaker
                score = 1e6 + self.evaluate(child.state)
            else:
                Q = child.value_sum / child.visits
                U = C * sqrt(log_N / child.visits)
                score = Q + U

            if score > best_score:
                best_score = score
                best = child

        return best

    # ------------------------------------------------------------------
    # Selection (tree policy)
    # ------------------------------------------------------------------
    def selection(self, node):
        current = node
        for _ in range(self.depth):
            if self.game_state.is_terminal(current.state):
                return current
            if current.untried or not current.children:
                return current
            current = self.best_child(current)
        return current

    # ------------------------------------------------------------------
    # Smart rollout
    # ------------------------------------------------------------------
    def simulate(self, node):
        state = node.state
        gs = self.game_state

        for _ in range(self.depth):
            if gs.is_terminal(state):
                return self.evaluate(state)

            phase = state['phase']
            conquered = state['conquered_country']
            player = gs.get_active_player_name(state)
            countries = state['countries']

            action = None

            # --- Conquered territory: move max-1 ---
            if conquered:
                max_m = countries[conquered['from']]['units'] - 1
                if max_m >= 1:
                    action = ("conquered_country", conquered['from'], conquered['to'], max_m)

            # --- PLACE: pick border with highest enemy pressure ---
            elif phase == 'place':
                available = state['players'][player]['available_units']
                if available <= 0:
                    action = ("skip_to_attack",)
                else:
                    if state['starting_phase']:
                        borders = gs._get_border_territories(state, player)
                        if not borders:
                            borders = [n for n, i in countries.items() if i['owner'] == player]
                        if borders:
                            best_border = max(borders, key=lambda b: gs._enemy_pressure(state, b))
                            action = ("place", best_border, 1)
                    else:
                        borders = gs._get_border_territories(state, player)
                        if not borders:
                            borders = [n for n, i in countries.items() if i['owner'] == player]
                        if borders:
                            best_border = max(borders, key=lambda b: gs._enemy_pressure(state, b))
                            action = ("place", best_border, available)
                        else:
                            action = ("skip_to_attack",)

            # --- ATTACK: 70% attack weakest neighbour if advantageous, 30% skip ---
            elif phase == 'attack':
                if random() < 0.70:
                    best_attack = None
                    best_ratio = 0
                    controlled = [n for n, i in countries.items() if i['owner'] == player]
                    for c in controlled:
                        my_units = countries[c]['units']
                        if my_units < 4:
                            continue
                        for nb in countries[c]['neighbours']:
                            if countries[nb]['owner'] != player:
                                enemy_units = countries[nb]['units']
                                if my_units > enemy_units:
                                    ratio = my_units / max(1, enemy_units)
                                    if ratio > best_ratio:
                                        best_ratio = ratio
                                        best_attack = ("attack", c, nb, min(my_units - 1, 3))
                    if best_attack:
                        action = best_attack
                    else:
                        action = ("skip_to_fortify",)
                else:
                    action = ("skip_to_fortify",)

            # --- FORTIFY: move from interior to most threatened border ---
            elif phase == 'fortify':
                if not state['fortified']:
                    borders_set = set(gs._get_border_territories(state, player))
                    # Find interior territories with spare units
                    best_move = None
                    best_pressure = -1
                    controlled = [n for n, i in countries.items() if i['owner'] == player]
                    for src in controlled:
                        if src in borders_set:
                            continue
                        if countries[src]['units'] <= 1:
                            continue
                        reachable = gs.get_all_neighbours(countries, src, player)
                        for dst in reachable:
                            if dst in borders_set:
                                p = gs._enemy_pressure(state, dst)
                                if p > best_pressure:
                                    best_pressure = p
                                    move_units = countries[src]['units'] - 1
                                    best_move = ("fortify", src, dst, move_units)
                    if best_move:
                        action = best_move
                    else:
                        action = ("end_turn",)
                else:
                    action = ("end_turn",)

            # Fallback: if no smart action found, pick from valid actions
            if action is None:
                valid = list(gs.get_valid_actions(state))
                if not valid:
                    break
                action = choice(valid)

            state = gs.apply_action(state, action)

        return self.evaluate(state)

    # ------------------------------------------------------------------
    # Backpropagation
    # ------------------------------------------------------------------
    def backpropagate(self, node, reward):
        cur = node
        while cur is not None:
            cur.visits += 1
            if cur.player_index == self.root_player_index:
                cur.value_sum += reward
            else:
                cur.value_sum -= reward
            cur = cur.parent

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def get_action(self):
        self.root_node.untried = self.game_state.get_valid_actions(self.root_node.state)
        if not self.root_node.untried:
            return "no available actions"

        for _ in range(self.n_iterations):
            node = self.selection(self.root_node)
            if node.untried or not node.children:
                node = self.expand(node)
            reward = self.simulate(node)
            self.backpropagate(node, reward)

        if not self.root_node.children:
            return "no children in root node"

        best_child = max(self.root_node.children, key=lambda c: c.visits)
        return best_child.action
