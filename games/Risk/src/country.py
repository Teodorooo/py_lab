from shapely.geometry import Point, Polygon
import pygame as pg
import pandas as pd
import json
import random
from src.utils import Utils
draw_text = Utils().draw_text

class Country:
    def __init__(self, name, owner, coords, color):
        self.name = name
        self.owner = owner
        self.coords = coords
        self.original_color = color
        self.color = color
        self.polygon = Polygon(self.coords)
        self.units = 1
        self.hovered = False
        self.selected = False
        self.neighbours = []
        self.center = self.get_center()

    def change_color_when_hovered(self):
        if self.hovered:
            self.color = [min(c + 50, 255) for c in self.original_color]
        else:

            self.color = self.original_color

    def check_hovered(self, mouse_pos: pg.Vector2, mouse_offset: pg.Vector2, mouse_clicked: bool, screen: object, font_path: str) -> None:
        self.selected = self.hovered and mouse_clicked
        is_hovering = Point(mouse_pos.x + mouse_offset.x, mouse_pos.y + mouse_offset.y).within(self.polygon)
        if is_hovering:
            self.show_country_info(screen, font_path)
        if is_hovering != self.hovered:
            self.hovered = is_hovering
            self.change_color_when_hovered()
            
    def show_country_info(self, screen, font_path):
        font_size = (screen.size[0] + screen.size[1]) * 0.015 / 2
        surf = pg.surface.Surface((screen.size[0], screen.size[1]))
        rect = surf.get_rect(topleft = (((screen.size[0] * 0.75, screen.size[1] * 0.75))))
        surf.set_alpha(210)
        screen.blit(surf, rect)
        draw_text(screen, font_path, font_size, f"Owner: {self.owner}", "white", screen.size[0] * 0.75, screen.size[1] * 0.75)

    def get_center(self) -> pg.Vector2:
        return pg.Vector2(
            pd.Series([x for x, y in self.coords]).mean(),
            pd.Series([y for x, y in self.coords]).mean(),
        )

class MakeCountries:
    def __init__(self, players):

            self.MAP_WIDTH = 2.05 * 4000
            self.MAP_HEIGHT = 1.0 * 4000
            self.players = players
            self.countries = []
            self.read_geo_data()
            self.assign_countries_to_player()
            self.create_countries()
            for country in self.countries:
                self.get_country_neighbours(country)    

    def create_countries(self) -> None:
        for name, coords in self.geo_data.items():
            for owner, info in self.players.items():
                for country_name in info['controlled_countries']:
                    if country_name == name:
                        xy_coords = []
                        for coord in coords:
                            x = (self.MAP_WIDTH / 360) * (180 + coord[0])
                            y = (self.MAP_HEIGHT / 180) * (90 - coord[1])
                            xy_coords.append(pg.Vector2(x, y))
                        self.countries.append(Country(name, owner, xy_coords, info['color']))
                        
    def assign_countries_to_player(self) -> None:
        all_starting_countries = list(self.geo_data.keys())
        random.shuffle(all_starting_countries)      
        num = 0
        
        for player_info in self.players.values():
            player_info["controlled_countries"] = all_starting_countries[
                int(num) : int(len(all_starting_countries) / len(self.players) + num)]
            num += len(all_starting_countries) / len(self.players) 
        
    def read_geo_data(self) -> None:
        with open("Risk/data/country_coords.json", "r") as f:
            self.geo_data = json.load(f)
            
    def get_country_neighbours(self, country: Country) -> dict:
        for other_country in self.countries:
            if country.name != other_country.name:
                if country.polygon.intersects(other_country.polygon):
                    country.neighbours.append(other_country)
                    
        overrides = {
            "United Kingdom": ["Ireland", "France", "Iceland"],
            "France": ["United Kingdom"],
            "Ireland": ["United Kingdom", "Iceland"],
            "Iceland": ["United Kingdom", "Ireland"],
            "Denmark": ["Norway", "Sweden"],
            "Norway": ["Denmark"],
            "Sweden": ["Denmark"],
            "Finland": ["Estonia"],
            "Estonia": ["Finland"],
        }
        name_to_country = {c.name: c for c in self.countries}
        
        if country.name in overrides:
            for neighbor_name in overrides[country.name]:
                if neighbor_name in name_to_country:
                    country.neighbours.append(name_to_country[neighbor_name])