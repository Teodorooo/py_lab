import pygame as pg
import src.theme as theme


class Draw:
    def __init__(self, screen, countries, font_path):
        self.screen = screen
        self.countries = countries
        self.font_path = font_path

        self.mouse_offset = pg.Vector2(3650, 395)
        self.offset_mouse_pos = pg.Vector2()
        self.mouse_pos = pg.Vector2(0, 0)
        self.zoom = 1.0
        self.min_zoom = 0.35
        self.max_zoom = 3.0

        self.hovered_country = None

    # ------------------------------------------------------------------ camera
    def screen_to_world(self, screen_pos):
        return pg.Vector2(screen_pos) / self.zoom + self.mouse_offset

    def world_to_screen(self, world_pos):
        return (pg.Vector2(world_pos) - self.mouse_offset) * self.zoom

    def zoom_at(self, screen_pos, scroll_amount):
        if scroll_amount == 0:
            return

        anchor_world_pos = self.screen_to_world(screen_pos)
        zoom_step = 1.12
        new_zoom = self.zoom * (zoom_step ** scroll_amount)
        self.zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        self.mouse_offset = anchor_world_pos - pg.Vector2(screen_pos) / self.zoom

    def update_camera(self):
        mouse_pressed = pg.mouse.get_pressed()
        mouse_pos = pg.mouse.get_pos()

        if mouse_pressed[0]:
            self.offset_mouse_pos.xy = mouse_pos[0], mouse_pos[1]
            delta = self.offset_mouse_pos - self.mouse_pos
            self.mouse_offset -= delta / self.zoom

        self.mouse_pos.xy = mouse_pos[0], mouse_pos[1]

    # ---------------------------------------------------------- country render
    def draw_countries(self):
        self.hovered_country = None

        for country in self.countries:
            shifted = [
                ((x - self.mouse_offset.x) * self.zoom,
                 (y - self.mouse_offset.y) * self.zoom)
                for x, y in country.coords
            ]

            # --- fill ---
            if country.hovered:
                fill = theme.darken(country.original_color, 0.55)
            else:
                fill = theme.darken(country.original_color, 0.3)

            pg.draw.polygon(self.screen, fill, shifted)

            # --- border ---
            if country.hovered:
                self.hovered_country = country

                # outer glow: faint ACCENT_GLOW at 4 px on a translucent surface
                bbox = _polygon_bbox(shifted)
                if bbox[2] > 0 and bbox[3] > 0:
                    glow_surf = pg.Surface((bbox[2], bbox[3]), pg.SRCALPHA)
                    local_pts = [(x - bbox[0], y - bbox[1]) for x, y in shifted]
                    pg.draw.polygon(
                        glow_surf,
                        (*theme.ACCENT_GLOW[:3], 25),
                        local_pts,
                        width=4,
                    )
                    self.screen.blit(glow_surf, (bbox[0], bbox[1]))

                # bright border
                pg.draw.polygon(
                    self.screen, country.original_color, shifted, width=2
                )
            else:
                border_color = theme.darken(country.original_color, 0.65)
                pg.draw.polygon(self.screen, border_color, shifted, width=1)

    # --------------------------------------------------------------- units
    def draw_units(self):
        for country in self.countries:
            cx, cy = self.world_to_screen(country.center)
            theme.unit_circle(self.screen, cx, cy, country.units, country.original_color)

    def is_action_bar_hovered(self):
        sw, sh = self.screen.get_size()
        bar_h = 48
        margin = 10
        rect = pg.Rect(margin, sh - bar_h - margin,
                       sw - margin * 2, bar_h)
        return rect.collidepoint(pg.mouse.get_pos())

    # --------------------------------------------------------------- tooltip
    def draw_tooltip(self):
        if self.hovered_country is None:
            return

        c = self.hovered_country
        sw, sh = self.screen.get_size()
        mx, my = pg.mouse.get_pos()

        pad = 12
        line_h = 22
        lines = [
            c.name,
            f"Owner: {c.owner}",
            f"Units: {c.units}",
            f"Neighbors: {len(c.neighbours)}",
        ]
        # measure width
        max_w = 0
        for line in lines:
            f = theme.font(14)
            tw, _ = f.size(line)
            if tw > max_w:
                max_w = tw

        panel_w = max_w + pad * 2
        panel_h = len(lines) * line_h + pad * 2

        # position near mouse, clamped to screen
        tx = mx + 16
        ty = my + 16
        if tx + panel_w > sw:
            tx = mx - panel_w - 8
        if ty + panel_h > sh:
            ty = my - panel_h - 8
        if tx < 0:
            tx = 0
        if ty < 0:
            ty = 0

        rect = pg.Rect(tx, ty, panel_w, panel_h)
        theme.glass_panel(self.screen, rect, alpha=200, border=theme.ACCENT_DIM)

        for i, line in enumerate(lines):
            color = theme.TEXT_BRIGHT if i == 0 else theme.TEXT
            theme.text(
                self.screen, line,
                tx + pad, ty + pad + i * line_h,
                size=14, color=color,
            )

    # ------------------------------------------------------------------- HUD
    def draw_hud(self, player_name, color, phase, army, territories, total):
        sw, sh = self.screen.get_size()
        panel_w = int(sw * 0.20)
        margin = 10
        panel_h = 200
        px = sw - panel_w - margin
        py = margin

        rect = pg.Rect(px, py, panel_w, panel_h)
        theme.glass_panel(self.screen, rect, alpha=190, border=theme.ACCENT_DIM)

        inner_x = px + 16
        cur_y = py + 14

        # --- player name with color indicator circle ---
        pg.draw.circle(self.screen, color, (inner_x + 6, cur_y + 9), 6)
        theme.text(self.screen, player_name, inner_x + 20, cur_y,
                   size=18, color=theme.TEXT_BRIGHT)
        cur_y += 32

        # --- phase indicator row ---
        phase_labels = ["Deploy", "Attack", "Fortify"]
        phase_keys = ["place", "attack", "fortify"]
        seg_w = (panel_w - 32) // 3
        for i, (label, key) in enumerate(zip(phase_labels, phase_keys)):
            seg_rect = pg.Rect(inner_x + i * seg_w, cur_y, seg_w - 4, 26)
            is_active = (phase == key)
            if is_active:
                theme.glass_panel(
                    self.screen, seg_rect, alpha=220,
                    border=theme.ACCENT, fill=(0, 160, 155),
                    radius=4,
                )
                theme.text(
                    self.screen, label,
                    seg_rect.centerx, seg_rect.centery,
                    size=13, color=theme.BG, center=True,
                )
            else:
                theme.glass_panel(
                    self.screen, seg_rect, alpha=120,
                    border=theme.ACCENT_DIM, fill=theme.BG_LIGHT,
                    radius=4,
                )
                theme.text(
                    self.screen, label,
                    seg_rect.centerx, seg_rect.centery,
                    size=13, color=theme.TEXT_DIM, center=True,
                )
        cur_y += 40

        # --- army count ---
        theme.text(self.screen, "Army", inner_x, cur_y,
                   size=12, color=theme.TEXT_DIM)
        theme.text(self.screen, str(army), inner_x + 60, cur_y,
                   size=28, color=theme.ACCENT)
        cur_y += 42

        # --- territory count ---
        theme.text(self.screen, "Territories", inner_x, cur_y,
                   size=12, color=theme.TEXT_DIM)
        theme.text(self.screen, f"{territories} / {total}",
                   inner_x + 90, cur_y,
                   size=16, color=theme.TEXT)

    # --------------------------------------------------------- phase button
    def draw_phase_button(self, mouse_clicked):
        btn_w, btn_h = 140, 36
        margin = 12
        rect = pg.Rect(margin, margin, btn_w, btn_h)

        mx, my = pg.mouse.get_pos()
        hovered = rect.collidepoint(mx, my)

        theme.button(self.screen, rect, "Next Phase",
                     size=15, hovered=hovered)

        if hovered and mouse_clicked:
            return True
        return False

    # --------------------------------------------------------- action bar
    def draw_action_bar(self, action_text, confirm_text="Confirm",
                        mouse_clicked=False):
        sw, sh = self.screen.get_size()
        bar_h = 48
        margin = 10
        bar_rect = pg.Rect(margin, sh - bar_h - margin,
                           sw - margin * 2, bar_h)

        theme.glass_panel(self.screen, bar_rect, alpha=200,
                          border=theme.ACCENT_DIM)

        # action text on the left, vertically centered
        f = theme.font(15)
        ts = f.render(str(action_text), True, theme.TEXT)
        tr = ts.get_rect(midleft=(bar_rect.x + 16, bar_rect.centery))
        self.screen.blit(ts, tr)

        # confirm button on the right
        btn_w = max(100, theme.font(15).size(confirm_text)[0] + 32)
        btn_rect = pg.Rect(
            bar_rect.right - btn_w - 8,
            bar_rect.y + 6,
            btn_w,
            bar_h - 12,
        )
        mx, my = pg.mouse.get_pos()
        hovered = btn_rect.collidepoint(mx, my)
        theme.button(self.screen, btn_rect, confirm_text,
                     size=15, hovered=hovered)

        if hovered and mouse_clicked:
            return True
        return False

    # --------------------------------------------------------- main update
    def update(self):
        self.update_camera()
        self.draw_countries()
        self.draw_units()


# --------------------------------------------------------------------- helpers
def _polygon_bbox(points):
    """Return (x, y, w, h) bounding box for a list of (x, y) tuples."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x = min(xs)
    min_y = min(ys)
    return (int(min_x), int(min_y),
            int(max(xs) - min_x) + 1,
            int(max(ys) - min_y) + 1)
