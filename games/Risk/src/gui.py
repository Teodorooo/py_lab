import pygame as pg
from pygame_gui.elements import UIButton
from pygame_gui.windows import UIColourPickerDialog
from shapely.geometry import Point, Polygon
from src.utils import Utils
from random import randint

draw_text = Utils().draw_text

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
    def __init__(player, 
                 ui_manager, 
                 screen,
                 x_divisions, 
                 y_divisions, 
                 player_num, 
                 name = "Pick Name", 
                 color = pg.Color(randint(0,255), randint(0,255), randint(0,255)), 
                 type = None, 
                 is_bot = True, 
                 version = None):
        
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
        avg_rgb = sum(player.color) / 3
        if avg_rgb > 127.5:
            inverted_player_color = (0, 0, 0)
        else:
            inverted_player_color = (255, 255, 255)

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