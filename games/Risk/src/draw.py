import pygame as pg
from src.utils import Utils
draw_text = Utils().draw_text

class Draw:
    def __init__(self, screen, countries, font_path):
        self.screen = screen
        self.countries = countries
        self.font_path = font_path
        
        self.mouse_offset = pg.Vector2(3650, 395)
        self.offset_mouse_pos = pg.Vector2()
        self.mouse_pos = pg.Vector2(0, 0)

    def update_camera(self) -> None:
        mouse_pressed = pg.mouse.get_pressed()
        mouse_pos = pg.mouse.get_pos()
        
        if mouse_pressed[0]:
            
            self.offset_mouse_pos.xy = mouse_pos[0], mouse_pos[1]
            
            self.mouse_offset.x = self.mouse_offset.x + (self.offset_mouse_pos.x - self.mouse_pos.x)*-1
            self.mouse_offset.y = self.mouse_offset.y + (self.offset_mouse_pos.y - self.mouse_pos.y)*-1
        
        self.mouse_pos.xy = mouse_pos[0], mouse_pos[1]
    
    def draw_countries(self) -> None:
        for country in self.countries:
            pg.draw.polygon(
                self.screen,
                country.color,
                [(x - self.mouse_offset.x, y - self.mouse_offset.y) for x, y in country.coords],
            )
            pg.draw.polygon(
                self.screen,
                (255, 255, 255),
                [(x - self.mouse_offset.x, y - self.mouse_offset.y) for x, y in country.coords],
                width=1,
            )
    
    def draw_units(self):
        for country in self.countries:
            draw_text(self.screen, self.font_path, 10, str(country.units), (0, 0, 0), country.center.x - self.mouse_offset.x, country.center.y - self.mouse_offset.y, center = True)
            
    def update(self):
        self.update_camera()
        self.draw_countries()
        self.draw_units()