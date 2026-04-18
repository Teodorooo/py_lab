import random
from itertools import combinations


CARD_TYPES = ("infantry", "cavalry", "artillery")
TRADE_BONUSES = [4, 6, 8, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]


class RiskCard:
    def __init__(self, territory, card_type):
        self.territory = territory  # str or None for wild
        self.card_type = card_type  # "infantry", "cavalry", "artillery", or "wild"

    def __repr__(self):
        if self.card_type == "wild":
            return "RiskCard(wild)"
        return f"RiskCard({self.territory!r}, {self.card_type!r})"


class RiskDeck:
    def __init__(self, territories):
        self.draw_pile = []
        self.discard_pile = []

        for i, territory in enumerate(territories):
            card_type = CARD_TYPES[i % len(CARD_TYPES)]
            self.draw_pile.append(RiskCard(territory, card_type))

        self.draw_pile.append(RiskCard(None, "wild"))
        self.draw_pile.append(RiskCard(None, "wild"))

        random.shuffle(self.draw_pile)

    def draw_card(self):
        if not self.draw_pile:
            if not self.discard_pile:
                return None
            self.draw_pile = self.discard_pile
            self.discard_pile = []
            random.shuffle(self.draw_pile)
        return self.draw_pile.pop()

    def return_cards(self, cards):
        self.discard_pile.extend(cards)


def _is_valid_set(cards):
    """Check if three cards form a valid trade set."""
    types = [c.card_type for c in cards]
    wilds = types.count("wild")

    if wilds >= 2:
        return True

    non_wild = [t for t in types if t != "wild"]

    if wilds == 1:
        # Any 2 non-wild cards + 1 wild is valid
        return True

    # No wilds: three of a kind or one of each
    if len(set(non_wild)) == 1:
        return True
    if len(set(non_wild)) == 3:
        return True

    return False


class CardManager:
    def __init__(self, territories):
        self.deck = RiskDeck(territories)
        self.hands = {}
        self.trade_count = 0

    def init_player(self, name):
        self.hands[name] = []

    def draw_card(self, player_name):
        card = self.deck.draw_card()
        if card is not None:
            self.hands[player_name].append(card)
        return card

    def must_trade(self, player_name):
        return len(self.hands[player_name]) >= 5

    def find_valid_sets(self, player_name):
        hand = self.hands[player_name]
        valid = []
        for combo in combinations(range(len(hand)), 3):
            cards = (hand[combo[0]], hand[combo[1]], hand[combo[2]])
            if _is_valid_set(cards):
                valid.append(cards)
        return valid

    def trade(self, player_name, cards):
        hand = self.hands[player_name]
        card_list = list(cards)

        if len(card_list) != 3 or not _is_valid_set(card_list):
            return 0

        for card in card_list:
            hand.remove(card)

        self.deck.return_cards(card_list)

        bonus_index = min(self.trade_count, len(TRADE_BONUSES) - 1)
        bonus = TRADE_BONUSES[bonus_index]
        self.trade_count += 1
        return bonus

    def auto_trade(self, player_name):
        valid_sets = self.find_valid_sets(player_name)
        if valid_sets:
            return self.trade(player_name, valid_sets[0])
        return 0

    def transfer_cards(self, from_player, to_player):
        self.hands[to_player].extend(self.hands[from_player])
        self.hands[from_player] = []

    def hand_size(self, player_name):
        return len(self.hands[player_name])
