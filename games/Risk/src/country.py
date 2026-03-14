import pygame as pg
import json
import random
from math import sqrt
from src.utils import Utils
draw_text = Utils().draw_text


class Country:
    def __init__(self, name, owner, coords, color):
        self.name = name
        self.owner = owner
        self.coords = coords
        self.original_color = color
        self.color = color
        self.polygon = XPolygon(self.coords)
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
        is_hovering = self.polygon.contains_point(mouse_pos.x + mouse_offset.x, mouse_pos.y + mouse_offset.y)

        if is_hovering != self.hovered:
            self.hovered = is_hovering
            self.change_color_when_hovered()
            
        if is_hovering:
            self.show_country_info(screen, font_path)

    def show_country_info(self, screen, font_path):
        font_size = (screen.size[0] + screen.size[1]) * 0.015 / 2
        surf = pg.surface.Surface((screen.size[0], screen.size[1]))
        rect = surf.get_rect(topleft=(((screen.size[0] * 0.75, screen.size[1] * 0.75))))
        surf.set_alpha(210)
        screen.blit(surf, rect)
        draw_text(screen, font_path, font_size, f"Owner: {self.owner}", "white", screen.size[0] * 0.75, screen.size[1] * 0.75)

    def get_center(self) -> pg.Vector2:
        """
        Finds the 'pole of inaccessibility' — the point inside the polygon
        that is farthest from any edge. This is the "meatiest" part of the
        country, perfect for placing a label.
        
        How it works:
        1. Cover the bounding box with a grid of cells
        2. For each cell center, measure distance to the nearest polygon edge
        3. The cell whose center is farthest from all edges is the best candidate
        4. Subdivide the most promising cells into smaller grids
        5. Repeat until we're precise enough
        
        Think of it like inflating a circle inside the polygon — the center
        of the biggest circle that fits is the pole of inaccessibility.
        """
        coords = self.coords
        polygon = self.polygon

        min_x = polygon.min_x
        min_y = polygon.min_y
        max_x = polygon.max_x
        max_y = polygon.max_y

        width = max_x - min_x
        height = max_y - min_y
        cell_size = min(width, height)

        if cell_size == 0:
            avg_x = sum(x for x, y in coords) / len(coords)
            avg_y = sum(y for x, y in coords) / len(coords)
            self.center = pg.Vector2(avg_x, avg_y)
            return self.center

        # Build initial grid of candidate cells
        cells = []
        x = min_x
        while x < max_x:
            y = min_y
            while y < max_y:
                cells.append(_Cell(x + cell_size / 2, y + cell_size / 2, cell_size, polygon))
                y += cell_size
            x += cell_size

        # Test the centroid as a starting candidate
        centroid_x = sum(x for x, y in coords) / len(coords)
        centroid_y = sum(y for x, y in coords) / len(coords)
        best = _Cell(centroid_x, centroid_y, 0, polygon)

        for cell in cells:
            if cell.dist > best.dist:
                best = cell

        # Subdivide promising cells until precision is reached
        precision = cell_size * 0.01

        while cells:
            next_cells = []
            for cell in cells:
                if cell.max_dist <= best.dist + precision:
                    continue

                half = cell.size / 4
                cx, cy = cell.x, cell.y
                for dx, dy in [(-half, -half), (half, -half), (-half, half), (half, half)]:
                    new_cell = _Cell(cx + dx, cy + dy, cell.size / 2, polygon)
                    if new_cell.dist > best.dist:
                        best = new_cell
                    if new_cell.max_dist > best.dist + precision:
                        next_cells.append(new_cell)

            cells = next_cells

        self.center = pg.Vector2(best.x, best.y)
        return self.center


class _Cell:
    """
    A square cell used in the pole of inaccessibility search.
    Each cell knows:
      - its center point (x, y)
      - its size
      - the signed distance from its center to the nearest polygon edge
        (positive = inside, negative = outside)
      - the maximum possible distance any point in this cell could have
    """
    def __init__(self, x, y, size, polygon):
        self.x = x
        self.y = y
        self.size = size
        self.dist = polygon.signed_distance(x, y)
        self.max_dist = self.dist + size * sqrt(2) / 2


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
                int(num): int(len(all_starting_countries) / len(self.players) + num)]
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


class XPolygon:
    def __init__(self, points):
        if len(points) < 3:
            raise ValueError("A polygon needs at least 3 points")

        self.points = points

        xs = [x for x, y in points]
        ys = [y for x, y in points]
        self.min_x = min(xs)
        self.max_x = max(xs)
        self.min_y = min(ys)
        self.max_y = max(ys)

        # Precompute edges: (x1, y1, x2, y2, ymin, ymax)
        self.edges = []
        n = len(points)
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            ymin = y1 if y1 < y2 else y2
            ymax = y2 if y1 < y2 else y1
            self.edges.append((x1, y1, x2, y2, ymin, ymax))

    def contains_point(self, px, py, include_boundary=True):
        """Check if a point is inside this polygon."""
        if px < self.min_x or px > self.max_x or py < self.min_y or py > self.max_y:
            return False

        inside = False

        for x1, y1, x2, y2, ymin, ymax in self.edges:
            if include_boundary and _point_on_segment(px, py, x1, y1, x2, y2):
                return True

            if py < ymin or py >= ymax:
                continue

            x_intersection = x1 + (py - y1) * (x2 - x1) / (y2 - y1)

            if x_intersection > px:
                inside = not inside

        return inside

    def signed_distance(self, px, py):
        """
        Distance from point (px, py) to the nearest polygon edge.
        Positive if inside, negative if outside.
        Used by the pole of inaccessibility algorithm.
        """
        min_dist_sq = float('inf')

        for x1, y1, x2, y2, _, _ in self.edges:
            dist_sq = _point_to_segment_dist_sq(px, py, x1, y1, x2, y2)
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq

        dist = sqrt(min_dist_sq)

        if self.contains_point(px, py, False):
            return dist
        else:
            return -dist

    def intersects(self, other):
        """
        Check if this polygon touches or overlaps another XPolygon.
        """
        # Quick bounding box rejection
        if (self.max_x < other.min_x or other.max_x < self.min_x or
                self.max_y < other.min_y or other.max_y < self.min_y):
            return False

        # Check if any edges cross
        for x1a, y1a, x2a, y2a, _, _ in self.edges:
            for x1b, y1b, x2b, y2b, _, _ in other.edges:
                if _segments_intersect(x1a, y1a, x2a, y2a, x1b, y1b, x2b, y2b):
                    return True

        # Check if one polygon is entirely inside the other
        if self.points:
            px, py = self.points[0]
            if other.contains_point(px, py, False):
                return True
        if other.points:
            px, py = other.points[0]
            if self.contains_point(px, py, False):
                return True

        return False


def _point_to_segment_dist_sq(px, py, x1, y1, x2, y2):
    """
    Squared distance from point (px, py) to line segment (x1,y1)-(x2,y2).
    
    Projects the point onto the infinite line defined by the segment,
    then clamps to the segment's endpoints if the projection falls outside.
    """
    dx = x2 - x1
    dy = y2 - y1
    len_sq = dx * dx + dy * dy

    if len_sq == 0:
        # Segment is a single point
        dx2 = px - x1
        dy2 = py - y1
        return dx2 * dx2 + dy2 * dy2

    # t = how far along the segment the closest point is (0.0 to 1.0)
    t = ((px - x1) * dx + (py - y1) * dy) / len_sq

    if t < 0:
        t = 0
    elif t > 1:
        t = 1

    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    dx2 = px - closest_x
    dy2 = py - closest_y
    return dx2 * dx2 + dy2 * dy2


def _point_on_segment(px, py, x1, y1, x2, y2, eps=1e-12):
    """Check if point (px, py) lies exactly on segment (x1,y1)-(x2,y2)."""
    cross = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
    if abs(cross) > eps:
        return False
    return (
        min(x1, x2) - eps <= px <= max(x1, x2) + eps and
        min(y1, y2) - eps <= py <= max(y1, y2) + eps
    )


def _segments_intersect(x1a, y1a, x2a, y2a, x1b, y1b, x2b, y2b):
    """Check if segment (x1a,y1a)-(x2a,y2a) crosses segment (x1b,y1b)-(x2b,y2b)."""
    def cross(ox, oy, ax, ay, bx, by):
        return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)

    d1 = cross(x1b, y1b, x2b, y2b, x1a, y1a)
    d2 = cross(x1b, y1b, x2b, y2b, x2a, y2a)
    d3 = cross(x1a, y1a, x2a, y2a, x1b, y1b)
    d4 = cross(x1a, y1a, x2a, y2a, x2b, y2b)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True

    return False