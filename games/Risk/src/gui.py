import json
import random
from pathlib import Path

import pygame as pg
from src import theme
from src.country import CONTINENT_COUNTRIES

NAMES_PATH = Path(__file__).resolve().parent.parent / "data" / "name_lists.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_name_lists():
    fallback = {"adjectives": [], "animals": []}
    try:
        with open(NAMES_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
    except Exception as e:
        print(f"[name_lists] Failed to load {NAMES_PATH}: {type(e).__name__}: {e}")
        return fallback
    adjectives = [n for n in loaded.get("adjectives", []) if isinstance(n, str) and n]
    animals = [n for n in loaded.get("animals", []) if isinstance(n, str) and n]
    return {"adjectives": adjectives, "animals": animals}


def _generate_player_color(player_num):
    """Golden-angle hue spacing for maximally distinct player colors."""
    hue = (player_num * 137.508) % 360
    color = pg.Color(0)
    color.hsva = (hue, 70, 85, 100)
    return color


def _point_in_polygon(px, py, coords):
    """Ray-casting point-in-polygon test (kept for non-rect hit testing)."""
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


# ---------------------------------------------------------------------------
# Grid math
# ---------------------------------------------------------------------------

def _grid_rect(width, height, cols, rows, index, pad):
    """Return a pg.Rect for grid cell *index* (row-major) with padding."""
    col = index % cols
    row = index // cols
    cell_w = (width - pad * (cols + 1)) / cols
    cell_h = (height - pad * (rows + 1)) / rows
    x = pad + col * (cell_w + pad)
    y = pad + row * (cell_h + pad)
    return pg.Rect(int(x), int(y), int(cell_w), int(cell_h))


# ---------------------------------------------------------------------------
# PlayerCard
# ---------------------------------------------------------------------------

class PlayerCard:
    def __init__(self, player_num, name="Pick Name"):
        self.num = player_num
        self.name = name
        self.color = _generate_player_color(player_num)
        self.type = None          # "human" or "bot" or None
        self.is_changing_name = False

        # Rects computed on layout
        self.rect = pg.Rect(0, 0, 0, 0)
        self.name_rect = pg.Rect(0, 0, 0, 0)
        self.human_btn_rect = pg.Rect(0, 0, 0, 0)
        self.bot_btn_rect = pg.Rect(0, 0, 0, 0)
        self.delete_btn_rect = pg.Rect(0, 0, 0, 0)
        self.name_txt_rect = None  # set after first render

    # --- layout --------------------------------------------------------

    def layout(self, rect):
        """Recompute sub-element rects from the card rect."""
        self.rect = pg.Rect(rect)
        pad = max(6, int(min(rect.w, rect.h) * 0.06))
        inner_x = rect.x + pad
        inner_y = rect.y + pad
        inner_w = rect.w - pad * 2
        inner_h = rect.h - pad * 2

        # Delete button (top-right corner)
        del_size = max(18, int(min(inner_w, inner_h) * 0.14))
        self.delete_btn_rect = pg.Rect(
            rect.right - pad - del_size, rect.y + pad,
            del_size, del_size
        )

        # Color stripe height
        stripe_h = max(4, int(inner_h * 0.03))

        # Name area: top portion (below stripe)
        name_h = max(20, int(inner_h * 0.28))
        self.name_rect = pg.Rect(inner_x, inner_y + stripe_h + 2,
                                 inner_w - del_size - pad, name_h)

        # Human / Bot buttons side by side below name area
        btn_top = self.name_rect.bottom + pad
        btn_h = max(24, int(inner_h * 0.26))
        half_w = (inner_w - pad) // 2
        self.human_btn_rect = pg.Rect(inner_x, btn_top, half_w, btn_h)
        self.bot_btn_rect = pg.Rect(inner_x + half_w + pad, btn_top, half_w, btn_h)

    # --- drawing -------------------------------------------------------

    def draw(self, surface, is_timer_on, mouse_clicked, mouse_pos):
        """Draw this card. Returns (name_selected, delete_selected)."""
        name_selected = False
        delete_selected = False

        # Glass panel background
        theme.glass_panel(surface, self.rect, alpha=180,
                          border=theme.ACCENT_DIM, border_w=1, radius=8)

        # Color stripe at top of card
        pad = max(6, int(min(self.rect.w, self.rect.h) * 0.06))
        stripe_rect = pg.Rect(self.rect.x + pad, self.rect.y + pad,
                               self.rect.w - pad * 2, max(4, int(self.rect.h * 0.03)))
        pg.draw.rect(surface, (self.color.r, self.color.g, self.color.b),
                     stripe_rect, border_radius=2)

        # Small color circle next to name
        circle_r = max(6, int(min(self.rect.w, self.rect.h) * 0.045))
        circle_cx = self.name_rect.right + circle_r + 4
        circle_cy = self.name_rect.centery
        if circle_cx + circle_r < self.rect.right - pad:
            pg.draw.circle(surface, (self.color.r, self.color.g, self.color.b),
                           (circle_cx, circle_cy), circle_r)
            pg.draw.circle(surface, theme.ACCENT_DIM,
                           (circle_cx, circle_cy), circle_r, 1)

        # --- Name area ---
        name_hovered = self.name_rect.collidepoint(mouse_pos.x, mouse_pos.y)

        if name_hovered and mouse_clicked:
            self.is_changing_name = True
            name_selected = True
        elif not name_hovered and mouse_clicked:
            self.is_changing_name = False

        # Draw name background when not editing
        if not self.is_changing_name:
            theme.glass_panel(surface, self.name_rect, alpha=100,
                              border=theme.ACCENT_DIM if name_hovered else theme.darken(theme.ACCENT_DIM),
                              border_w=1, radius=4, fill=theme.BG_LIGHT)

        if self.is_changing_name:
            theme.glass_panel(surface, self.name_rect, alpha=140,
                              border=theme.ACCENT, border_w=1, radius=4,
                              fill=(20, 30, 55))

        # Render name text
        font_size = max(10, int(self.name_rect.h * 0.55))
        name_x = self.name_rect.x + max(4, int(self.name_rect.w * 0.04))
        name_color = theme.TEXT_BRIGHT if self.is_changing_name else theme.TEXT_BRIGHT
        name_font = theme.font(font_size)
        measured_rect = name_font.render(str(self.name), True, name_color).get_rect()
        txt_y = self.name_rect.centery - measured_rect.height // 2
        self.name_txt_rect = theme.text(
            surface, self.name, name_x, txt_y,
            size=font_size, color=name_color, center=False
        )

        # Cursor blink
        if self.is_changing_name and is_timer_on and self.name_txt_rect is not None:
            cursor_x = self.name_txt_rect.right + 2
            cursor_top = self.name_txt_rect.top
            cursor_bot = self.name_txt_rect.bottom
            pg.draw.line(surface, theme.ACCENT_GLOW,
                         (cursor_x, cursor_top), (cursor_x, cursor_bot), 2)

        # --- Human / Bot buttons ---
        human_hovered = self.human_btn_rect.collidepoint(mouse_pos.x, mouse_pos.y)
        bot_hovered = self.bot_btn_rect.collidepoint(mouse_pos.x, mouse_pos.y)

        btn_font_size = max(10, int(self.human_btn_rect.h * 0.45))

        theme.button(surface, self.human_btn_rect, "Human",
                     size=btn_font_size,
                     hovered=human_hovered,
                     active=(self.type == "human"),
                     accent=theme.ACCENT)
        theme.button(surface, self.bot_btn_rect, "Bot",
                     size=btn_font_size,
                     hovered=bot_hovered,
                     active=(self.type == "bot"),
                     accent=theme.ACCENT)

        if human_hovered and mouse_clicked:
            self.type = "human"
        if bot_hovered and mouse_clicked:
            self.type = "bot"

        # --- Delete button ---
        del_hovered = self.delete_btn_rect.collidepoint(mouse_pos.x, mouse_pos.y)
        del_font_size = max(10, int(self.delete_btn_rect.h * 0.55))
        theme.button(surface, self.delete_btn_rect, "X",
                     size=del_font_size,
                     hovered=del_hovered,
                     active=False,
                     accent=theme.DANGER)

        if del_hovered and mouse_clicked:
            delete_selected = True

        return name_selected, delete_selected


# ---------------------------------------------------------------------------
# ManageCards  (main settings screen controller)
# ---------------------------------------------------------------------------

class ManageCards:
    def __init__(self, screen):
        self.screen = screen
        self.cols = 3
        self.rows = 2
        self.player_count = 1  # 0-based index of last player (starts with 2 players: indices 0,1)
        self.name_lists = _load_name_lists()
        self.used_names = set()

        self.player_cards = [
            PlayerCard(n, name=self.generate_default_name())
            for n in range(self.player_count + 1)
        ]

        self.changed_card_name = None
        self.card_size_updated = True
        self.settings_selected = False
        self.selected_map = "World"
        self.show_map_screen = False
        self.players = {}

    # --- public interface ------------------------------------------------

    def draw_cards(self, screen, width, height, mouse_clicked, is_timer_on, font_path):
        """Called each frame while the settings screen is active."""
        mouse_pos = pg.Vector2(pg.mouse.get_pos())

        # Draw dark gradient background
        theme.draw_gradient(screen)

        if self.show_map_screen:
            self._draw_map_screen(screen, width, height, mouse_clicked, mouse_pos)
            return

        pad = max(8, int((width + height) * 0.012))

        # Total grid slots = rows * cols
        # Reserve last 3 slots for: Add Player, Map, Start
        total_slots = self.rows * self.cols

        if self.card_size_updated:
            self._layout_all(width, height, pad)
            self.card_size_updated = False

        # Draw player cards
        for card in self.player_cards:
            name_sel, del_sel = card.draw(screen, is_timer_on, mouse_clicked, mouse_pos)
            if name_sel:
                self.changed_card_name = card
            if del_sel:
                self._delete_player(card)
                break

        # Bottom buttons: Add Player, Map, Start
        self._draw_bottom_buttons(screen, width, height, pad, mouse_clicked, mouse_pos)

    def change_player_name(self, key):
        """Handle KEYDOWN events for the currently editing card name."""
        if not self.changed_card_name:
            return
        card = self.changed_card_name
        if not card.is_changing_name:
            return

        # Check if more text fits within the name area
        key_fits = True
        if card.name_txt_rect is not None and card.name_rect.w > 0:
            key_fits = card.name_txt_rect.right < card.name_rect.right - 8

        if key == "backspace":
            card.name = card.name[:-1]
        elif key == "space":
            if key_fits:
                card.name += " "
        elif key == "return" or key == "escape":
            card.is_changing_name = False
        elif len(key) > 1:
            return
        else:
            if key_fits:
                card.name += key

    # --- name generation -------------------------------------------------

    def generate_default_name(self):
        adjectives = self.name_lists["adjectives"]
        animals = self.name_lists["animals"]
        if adjectives and animals:
            possible = [f"{adj} {ani}" for adj in adjectives for ani in animals]
            unused = [n for n in possible if n.lower() not in self.used_names]
            if unused:
                chosen = random.choice(unused)
            else:
                chosen = random.choice(possible)
                suffix = 2
                while f"{chosen} {suffix}".lower() in self.used_names:
                    suffix += 1
                chosen = f"{chosen} {suffix}"
        else:
            base = "Player"
            suffix = 1
            chosen = f"{base} {suffix}"
            while chosen.lower() in self.used_names:
                suffix += 1
                chosen = f"{base} {suffix}"
        self.used_names.add(chosen.lower())
        return chosen

    # --- private: layout -------------------------------------------------

    def _layout_all(self, width, height, pad):
        """Compute layout rects for all player cards."""
        for card in self.player_cards:
            rect = _grid_rect(width, height, self.cols, self.rows, card.num, pad)
            card.layout(rect)

    # --- private: bottom buttons -----------------------------------------

    def _draw_bottom_buttons(self, screen, width, height, pad, mouse_clicked, mouse_pos):
        total_slots = self.rows * self.cols

        # Add Player: slot after last player
        add_idx = self.player_count + 1
        add_rect = _grid_rect(width, height, self.cols, self.rows, add_idx, pad)
        add_hovered = add_rect.collidepoint(mouse_pos.x, mouse_pos.y)
        theme.button(screen, add_rect, "+ Add Player",
                     size=max(12, int(add_rect.h * 0.12)),
                     hovered=add_hovered, accent=theme.SUCCESS)
        if add_hovered and mouse_clicked:
            self._add_player()

        # Map button: second-to-last slot
        map_idx = total_slots - 2
        map_rect = _grid_rect(width, height, self.cols, self.rows, map_idx, pad)
        map_hovered = map_rect.collidepoint(mouse_pos.x, mouse_pos.y)
        theme.button(screen, map_rect, f"Map: {self.selected_map}",
                     size=max(12, int(map_rect.h * 0.12)),
                     hovered=map_hovered, accent=theme.ACCENT)
        if map_hovered and mouse_clicked:
            self.show_map_screen = True

        # Start button: last slot
        start_idx = total_slots - 1
        start_rect = _grid_rect(width, height, self.cols, self.rows, start_idx, pad)
        start_hovered = start_rect.collidepoint(mouse_pos.x, mouse_pos.y)
        theme.button(screen, start_rect, "Start",
                     size=max(14, int(start_rect.h * 0.15)),
                     hovered=start_hovered, accent=theme.ACCENT)
        if start_hovered and mouse_clicked:
            self._start_game()

    # --- private: actions ------------------------------------------------

    def _start_game(self):
        self.settings_selected = True
        self.players = {
            card.name: {
                "bot_version": None if card.type == "human" else "newmcts",
                "color": (card.color.r, card.color.g, card.color.b)
            }
            for card in self.player_cards
        }

    def _add_player(self):
        self.player_count += 1
        # Expand grid if we run out of card slots (need 3 reserved for buttons)
        if self.player_count >= self.cols * self.rows - 3:
            if self.cols - self.rows >= 2:
                self.rows += 1
            else:
                self.cols += 1
            self.card_size_updated = True

        new_card = PlayerCard(self.player_count, name=self.generate_default_name())
        self.player_cards.append(new_card)
        self.card_size_updated = True

    def _delete_player(self, card):
        if len(self.player_cards) <= 2:
            return
        if card in self.player_cards:
            self.player_cards.remove(card)
            if not any(c.name.lower() == card.name.lower() for c in self.player_cards):
                self.used_names.discard(card.name.lower())
        self.changed_card_name = None
        self._reindex_cards()

    def _reindex_cards(self):
        self.player_count = len(self.player_cards) - 1
        for idx, card in enumerate(self.player_cards):
            card.num = idx
            card.color = _generate_player_color(idx)
        self.card_size_updated = True

    # --- private: map selection screen -----------------------------------

    def _draw_map_screen(self, screen, width, height, mouse_clicked, mouse_pos):
        """Full-screen overlay for map selection."""
        maps = list(CONTINENT_COUNTRIES.keys())
        cols = 2
        rows = (len(maps) + cols - 1) // cols
        pad = max(10, int((width + height) * 0.02))

        # Reserve space for back button row
        total_rows = rows + 1
        cell_w = (width - pad * (cols + 1)) / cols
        cell_h = (height - pad * (total_rows + 1)) / total_rows

        for idx, map_name in enumerate(maps):
            col = idx % cols
            row = idx // cols
            x = int(pad + col * (cell_w + pad))
            y = int(pad + row * (cell_h + pad))
            rect = pg.Rect(x, y, int(cell_w), int(cell_h))

            is_selected = (map_name == self.selected_map)
            hovered = rect.collidepoint(mouse_pos.x, mouse_pos.y)

            if is_selected:
                fill = (20, 40, 50)
                border_col = theme.ACCENT_GLOW
            elif hovered:
                fill = (28, 36, 60)
                border_col = theme.ACCENT
            else:
                fill = theme.PANEL
                border_col = theme.ACCENT_DIM

            theme.glass_panel(screen, rect, alpha=200, border=border_col,
                              border_w=2 if is_selected else 1, radius=8, fill=fill)

            if is_selected:
                theme.glow_rect(screen, rect, color=theme.ACCENT_GLOW, width=1, radius=8)

            font_size = max(14, int(min(cell_w, cell_h) * 0.18))
            theme.text(screen, map_name,
                       rect.centerx, rect.centery,
                       size=font_size,
                       color=theme.TEXT_BRIGHT if is_selected else theme.TEXT,
                       center=True)

            if hovered and mouse_clicked:
                self.selected_map = map_name

        # Back button (full width bottom row)
        back_y = int(pad + rows * (cell_h + pad))
        back_rect = pg.Rect(int(pad), back_y,
                            int(width - 2 * pad), int(cell_h))
        back_hovered = back_rect.collidepoint(mouse_pos.x, mouse_pos.y)
        back_font = max(14, int(cell_h * 0.22))
        theme.button(screen, back_rect, "Back",
                     size=back_font, hovered=back_hovered,
                     accent=theme.DANGER)

        if back_hovered and mouse_clicked:
            self.show_map_screen = False
