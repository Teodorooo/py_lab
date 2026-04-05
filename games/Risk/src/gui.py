import json
import random
from pathlib import Path

import pygame as pg
from src.utils import Utils

draw_text = Utils().draw_text
NAMES_PATH = Path(__file__).resolve().parent.parent / "data" / "name_lists.json"


def _load_name_lists():
    fallback = {
        "adjectives": [],
        "animals": []
    }

    try:
        with open(NAMES_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback

    adjectives = [name for name in loaded.get("adjectives", []) if isinstance(name, str) and name]
    animals = [name for name in loaded.get("animals", []) if isinstance(name, str) and name]

    return {
        "adjectives": adjectives,
        "animals": animals
    }


def _point_in_polygon(px, py, coords):
    """Simple ray-casting point-in-polygon check."""
    n = len(coords)
    inside = False
    p1x, p1y = coords[0][0], coords[0][1]
    for i in range(1, n + 1):
        p2x, p2y = coords[i % n][0], coords[i % n][1]
        if py > min(p1y, p2y):
            if py <= max(p1y, p2y):
                if px <= max(p1x, p2x):
                    if p1y != p2y:
                        x_int = (py - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or px <= x_int:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def _generate_player_color(player_num):
    """
    Generate a color for a player that is maximally distant from all other
    player colors.
    
    Uses the golden angle (137.508 degrees) to space hues around the color
    wheel. This works because the golden angle is the most "irrational" 
    angle — it guarantees that no matter how many players you add, each new
    color lands as far as possible from all existing ones.
    
    It's the same reason sunflower seeds spiral in golden angle increments —
    maximum packing efficiency.
    """
    hue = (player_num * 137.508) % 360
    color = pg.Color(0)
    color.hsva = (hue, 70, 85, 100)
    return color


class ManageCards:
    def __init__(self, screen):
        self.x_divisions = 3
        self.y_divisions = 2
        self.player_count = 2
        self.name_lists = _load_name_lists()
        self.used_names = set()
        self.player_cards = [PlayerCard(screen, self.x_divisions, self.y_divisions, n, name=self.generate_default_name()) for n in range(self.player_count)]
        self.player_count -= 1
        self.screen = screen
        self.changed_card_name = None
        self.card_size_updated = False
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

            if getattr(card, "delete_selected_this_frame", False):
                self.delete_player(card)
                break

        self.add_button(screen, width, height, mouse_clicked, font_path, "Add Player", self.player_count + 1, self.add_player)
        self.add_button(screen, width, height, mouse_clicked, font_path, "Start", self.y_divisions * self.x_divisions - 1, self.start_game)

    def generate_default_name(self):
        adjectives = self.name_lists["adjectives"]
        animals = self.name_lists["animals"]

        if adjectives and animals:
            possible_names = [f"{adj} {animal}" for adj in adjectives for animal in animals]
            unused_names = [name for name in possible_names if name.lower() not in self.used_names]

            if unused_names:
                chosen_name = random.choice(unused_names)
            else:
                chosen_name = random.choice(possible_names)
                suffix = 2
                while f"{chosen_name} {suffix}".lower() in self.used_names:
                    suffix += 1
                chosen_name = f"{chosen_name} {suffix}"
        else:
            base_name = "Player"
            suffix = 1
            chosen_name = f"{base_name} {suffix}"
            while chosen_name.lower() in self.used_names:
                suffix += 1
                chosen_name = f"{base_name} {suffix}"

        self.used_names.add(chosen_name.lower())
        return chosen_name

    def start_game(self, _):
        self.settings_selected = True
        self.players = {
            f'{card.name}': {
                "bot_version": None if card.type == "human" else "newmcts",
                "color": (card.color.r, card.color.g, card.color.b)
            }
            for card in self.player_cards
        }

    def update_card_size(self, card, width, height):
        card.update_card_coords(width, height, self.x_divisions, self.y_divisions)
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

        if _point_in_polygon(mouse_pos.x, mouse_pos.y, coords):
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

        new_player = PlayerCard(screen, self.x_divisions, self.y_divisions, self.player_count, name=self.generate_default_name())
        self.player_cards.append(new_player)

    def delete_player(self, card):
        if len(self.player_cards) <= 2:
            return

        if card in self.player_cards:
            self.player_cards.remove(card)
            if not any(other.name.lower() == card.name.lower() for other in self.player_cards):
                self.used_names.discard(card.name.lower())

        self.changed_card_name = None
        self.reindex_cards()

    def reindex_cards(self):
        self.player_count = len(self.player_cards) - 1

        for idx, card in enumerate(self.player_cards):
            card.num = idx
            card.color = _generate_player_color(idx)
            card.update_card_coords(self.screen.size[0], self.screen.size[1], self.x_divisions, self.y_divisions)

        self.card_size_updated = False

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
    def __init__(player,
                 screen,
                 x_divisions,
                 y_divisions,
                 player_num,
                 name="Pick Name",
                 type=None,
                 is_bot=True,
                 version=None):

        player.screen = screen
        player.name = name
        player.color = _generate_player_color(player_num)
        player.type = type
        player.is_bot = is_bot
        player.version = version
        player.num = player_num
        player.x_divisions = x_divisions
        player.y_divisions = y_divisions
        player.is_changing_name = False
        player.xy_pos_updated = False

        player.name_info = None
        player.name_txt_rect = None
        player.name_selected_this_frame = False
        player.delete_selected_this_frame = False
        player.delete_coords = None

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

        pg.draw.line(screen, color, ((player.topleft.x + (player.topright.x - player.topleft.x) * 1 / 3),
                                     (player.topleft.y + (player.bottomleft.y - player.topleft.y) * 0.2 + player.shrink_amount)),
                     ((player.topleft.x + (player.topright.x - player.topleft.x) * 1 / 3),
                      player.bottomleft.y - player.shrink_amount),
                     3)

        pg.draw.line(screen, color, ((player.topleft.x + (player.topright.x - player.topleft.x) * 2 / 3),
                                     (player.topleft.y + (player.bottomleft.y - player.topleft.y) * 0.2 + player.shrink_amount)),
                     ((player.topleft.x + (player.topright.x - player.topleft.x) * 2 / 3),
                      player.bottomleft.y - player.shrink_amount),
                     3)

        pg.draw.line(screen, color, ((player.topleft.x + (player.topright.x - player.topleft.x) * 1 / 3),
                                     ((player.topleft.y + ((player.bottomleft.y - player.topleft.y)) * 6 / 10))),
                     ((player.topleft.x + (player.topright.x - player.topleft.x) * 2 / 3),
                      ((player.topleft.y + ((player.bottomleft.y - player.topleft.y)) * 6 / 10))),
                     3)

    def draw_card_info_txt(player, screen, inverted_color, is_timer_on, mouse_clicked, font_path, mouse_pos):
        player.name_selected_this_frame = False
        player.delete_selected_this_frame = False
        player.draw_delete_button(screen, inverted_color, mouse_clicked, font_path, mouse_pos)

        for info in player.infos:
            info.hovered = _point_in_polygon(mouse_pos.x, mouse_pos.y, info.coords)

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

    def draw_delete_button(player, screen, inverted_color, mouse_clicked, font_path, mouse_pos):
        delete_size = player.shrink_amount * 0.9
        top = player.topleft.y + player.shrink_amount * 0.4
        right = player.topright.x - player.shrink_amount * 0.4

        player.delete_coords = (
            (right - delete_size, top),
            (right, top),
            (right, top + delete_size),
            (right - delete_size, top + delete_size)
        )

        hovered = _point_in_polygon(mouse_pos.x, mouse_pos.y, player.delete_coords)
        fill_color = inverted_color if hovered else player.color
        text_color = player.color if hovered else inverted_color

        pg.draw.polygon(screen, fill_color, player.delete_coords)
        pg.draw.polygon(screen, inverted_color, player.delete_coords, 2)
        draw_text(
            screen,
            font_path,
            delete_size * 0.7,
            "X",
            text_color,
            right - delete_size * 0.72,
            top + delete_size * 0.08
        )

        if hovered and mouse_clicked:
            player.delete_selected_this_frame = True

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
             (player.topright.x - player.shrink_amount,
              (player.topright.y + (player.bottomright.y - player.topright.y) * 0.2) + player.shrink_amount),
             (player.topleft.x + player.shrink_amount,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 0.2 + player.shrink_amount)),
            player.name,
            is_text=True
        )

        human = PlayerInfo(
            ((player.topleft.x + (player.topright.x - player.topleft.x) * 1 / 3,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 0.2 + player.shrink_amount),
             (player.topleft.x + (player.topright.x - player.topleft.x) * 1 / 3,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 6 / 10),
             (player.topleft.x + (player.topright.x - player.topleft.x) * 2 / 3,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 6 / 10),
             (player.topleft.x + (player.topright.x - player.topleft.x) * 2 / 3,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 0.2 + player.shrink_amount)),
            "human",
            is_button=True,
            group_key="player_type"
        )

        bot = PlayerInfo(
            ((player.topleft.x + (player.topright.x - player.topleft.x) * 1 / 3,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 6 / 10),
             (player.topleft.x + (player.topright.x - player.topleft.x) * 2 / 3,
              player.topleft.y + (player.bottomleft.y - player.topleft.y) * 6 / 10),
             (player.topleft.x + (player.topright.x - player.topleft.x) * 2 / 3,
              player.bottomleft.y - player.shrink_amount),
             (player.topleft.x + (player.topright.x - player.topleft.x) * 1 / 3,
              player.bottomleft.y - player.shrink_amount)),
            "bot",
            is_button=True,
            group_key="player_type"
        )

        player.infos = [name, human, bot]
        player.name_info = name
        player.xy_pos_updated = False

    def draw_card(player, screen, is_timer_on, mouse_clicked, font_path, mouse_pos):
        avg_rgb = sum(player.color) / 3
        if avg_rgb > 127.5:
            inverted_player_color = (0, 0, 0)
        else:
            inverted_player_color = (255, 255, 255)

        player.draw_card_lines(screen, inverted_player_color)
        player.draw_card_info_txt(screen, inverted_player_color, is_timer_on, mouse_clicked, font_path, mouse_pos)

        if not player.xy_pos_updated:
            player.xy_pos_updated = True


def get_card_coords(width, height, xd, yd, num):
    topleft = pg.Vector2(((num % yd) % 100) / yd * width, (int(num / yd)) / xd * height)
    topright = pg.Vector2((((num % yd) + 1) % 100) / yd * width, (int(num / yd)) / xd * height)
    bottomleft = pg.Vector2(((num % yd) % 100) / yd * width, (int(num / yd) + 1) / xd * height)
    bottomright = pg.Vector2((((num % yd) + 1) % 100) / yd * width, (int(num / yd) + 1) / xd * height)
    return topleft, topright, bottomleft, bottomright
