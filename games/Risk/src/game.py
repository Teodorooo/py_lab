import pygame as pg
import asyncio
from src.draw import Draw
from src.country import MakeCountries
from src.gui import ManageCards
from src.player import PlayerManager
import src.theme as theme


class Game:
    def __init__(self, clock, bot_versions, screen):
        self.clock = clock
        self.bot_versions = bot_versions
        self.screen = screen
        self.font_path = theme.get_font_path()

        self.width, self.height = screen.get_size()

        self.playing = True
        self.scroll = 0
        self.game_over = False

        self.is_timer_on = False
        self.timer_last_toggle = pg.time.get_ticks()

        self.manage_cards = ManageCards(screen)
        self.mouse_clicked = False

    def init_game(self):
        players = self.manage_cards.players
        map_name = self.manage_cards.selected_map
        self.countries = MakeCountries(players, map_name).countries
        self.draw = Draw(self.screen, self.countries, self.font_path)
        self.manage_players = PlayerManager(
            self.screen, players, self.countries,
            self.bot_versions, self.font_path, self.draw
        )

    async def run(self):
        while self.playing:
            current_width, current_height = self.screen.get_size()
            if (current_width, current_height) != (self.width, self.height):
                self.width, self.height = current_width, current_height
                self.manage_cards.card_size_updated = True
                theme.invalidate_cache()

            # dark gradient background
            theme.draw_gradient(self.screen)
            self.events()

            now = pg.time.get_ticks()
            if now - self.timer_last_toggle >= 500:
                self.is_timer_on = not self.is_timer_on
                self.timer_last_toggle = now

            if not self.manage_cards.settings_selected:
                self.manage_cards.draw_cards(
                    self.screen, self.width, self.height,
                    self.mouse_clicked, self.is_timer_on, self.font_path
                )
                if self.manage_cards.settings_selected:
                    self.init_game()

            elif self.game_over:
                self.draw.update()
                self.win_screen(self._winner)

            else:
                mouse_pos = pg.Vector2(pg.mouse.get_pos())
                player_scroll = self.scroll
                if self.scroll and not self.manage_players.should_use_scroll_for_action():
                    self.draw.zoom_at(mouse_pos, self.scroll)
                    player_scroll = 0

                world_mouse_pos = self.draw.screen_to_world(mouse_pos)
                for country in self.countries:
                    country.check_hovered(
                        world_mouse_pos, self.mouse_clicked
                    )
                self.draw.update()
                self.manage_players.handle_player_turns(self.mouse_clicked, player_scroll)

                # tooltip drawn last (on top)
                self.draw.draw_tooltip()

                winner = self.manage_players.check_player_wins(len(self.countries))
                if winner:
                    self._winner = winner
                    self.game_over = True

            self.scroll = 0
            self.mouse_clicked = False

            await asyncio.sleep(0)
            pg.display.update()

    def win_screen(self, winning_player):
        # dark overlay on top of the map
        overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        overlay.fill((10, 14, 26, 200))
        self.screen.blit(overlay, (0, 0))

        # centered glass panel
        pw, ph = min(500, int(self.width * 0.45)), 200
        px = (self.width - pw) // 2
        py = (self.height - ph) // 2
        rect = pg.Rect(px, py, pw, ph)
        theme.glass_panel(self.screen, rect, alpha=230, border=theme.ACCENT, radius=12)
        theme.glow_rect(self.screen, rect, color=winning_player.color, radius=12)

        # "VICTORY" title
        theme.text(self.screen, "VICTORY", rect.centerx, py + 45,
                   size=36, color=theme.GOLD, center=True)

        # player name with color circle
        pg.draw.circle(self.screen, winning_player.color,
                       (rect.centerx - 60, py + 95), 10)
        theme.text(self.screen, winning_player.player_name,
                   rect.centerx - 42, py + 85, size=22, color=theme.TEXT_BRIGHT)

        # territory count
        theme.text(self.screen, f"{len(winning_player.controlled_countries)} territories conquered",
                   rect.centerx, py + 140, size=14, color=theme.TEXT_DIM, center=True)

        theme.text(self.screen, "Close the window to exit",
                   rect.centerx, py + 170, size=11, color=theme.TEXT_DIM, center=True)

    def events(self):
        self.clock.tick(60)
        for event in pg.event.get():
            if event.type == pg.VIDEORESIZE:
                self.width, self.height = event.size
                self.screen = pg.display.set_mode(
                    (self.width, self.height), pg.RESIZABLE
                )
                self.manage_cards.card_size_updated = True
                theme.invalidate_cache()

            if event.type == pg.QUIT:
                self.playing = False

            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                self.mouse_clicked = True

            if event.type == pg.MOUSEWHEEL:
                self.scroll = event.dict['y']

            if event.type == pg.KEYDOWN:
                self.manage_cards.change_player_name(pg.key.name(event.key))
