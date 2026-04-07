from random import randint
import pygame as pg

class Utils:
    def __init__(self):
        # cache: key = (font_path, size) -> pg.font.Font
        self._fonts = {}

    def attack_calculation(self, deployed_units, defender_units, attacker_units) -> int:
        attacker_rolls = sorted([randint(1, 6) for _ in range(deployed_units)], reverse=True)
        defender_rolls = sorted([randint(1, 6) for _ in range(min(2, defender_units))], reverse=True)

        for attack_roll, defense_roll in zip(attacker_rolls, defender_rolls):
            if attack_roll > defense_roll:
                defender_units -= 1
            else:
                attacker_units -= 1

        return defender_units, attacker_units

    def _font(self, font_path: str, size: int) -> pg.font.Font:
        safe_size = max(1, int(size))
        key = (font_path, safe_size)
        if key not in self._fonts:
            self._fonts[key] = pg.font.Font(font_path, safe_size)
        return self._fonts[key]

    def draw_text(
        self,
        screen: pg.Surface,
        font_path: str,
        size: int,
        text: str,
        color: tuple,
        x: int,
        y: int,
        center: bool = False,
        rect_color: tuple = None,
        get_hovered: bool = False,
        get_rect: bool = False,
    ):

        text_surf = self._font(font_path, size).render(text, True, color)
        text_rect = text_surf.get_rect()

        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)

        if rect_color:
            pg.draw.rect(screen, rect_color, text_rect)

        screen.blit(text_surf, text_rect)

        if get_rect and get_hovered:
            return text_rect.collidepoint(pg.mouse.get_pos()), text_rect

        if get_rect:
            return text_rect

        if get_hovered:
            return text_rect.collidepoint(pg.mouse.get_pos())
