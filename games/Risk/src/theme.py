import pygame as pg

# === Color Palette: Dark Tech Glass ===
BG = (10, 14, 26)
BG_LIGHT = (18, 24, 46)
ACCENT = (0, 210, 210)
ACCENT_DIM = (0, 110, 110)
ACCENT_GLOW = (0, 255, 255)
TEXT = (200, 215, 230)
TEXT_DIM = (90, 110, 130)
TEXT_BRIGHT = (240, 248, 255)
PANEL = (14, 20, 40)
PANEL_ALPHA = 180
DANGER = (210, 50, 50)
SUCCESS = (50, 200, 90)
GOLD = (230, 200, 60)

_gradient_cache = {}
_font_cache = {}
_font_path = None


def get_font_path():
    global _font_path
    if _font_path:
        return _font_path
    import os
    for p in ("font/Rajdhani-Medium.ttf", "font/Orbitron-Regular.ttf"):
        if os.path.exists(p):
            _font_path = p
            return p
    for name in ("segoeui", "calibri", "arial", "helvetica", "verdana"):
        match = pg.font.match_font(name, bold=True)
        if match:
            _font_path = match
            return match
        match = pg.font.match_font(name)
        if match:
            _font_path = match
            return match
    _font_path = pg.font.get_default_font()
    return _font_path


def font(size):
    size = max(1, int(size))
    path = get_font_path()
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = pg.font.Font(path, size)
    return _font_cache[key]


def draw_gradient(surface, top=BG, bottom=None):
    if bottom is None:
        bottom = BG_LIGHT
    w, h = surface.get_size()
    key = (w, h, top, bottom)
    if key not in _gradient_cache:
        grad = pg.Surface((w, h))
        for y in range(h):
            t = y / max(h - 1, 1)
            r = int(top[0] + (bottom[0] - top[0]) * t)
            g = int(top[1] + (bottom[1] - top[1]) * t)
            b = int(top[2] + (bottom[2] - top[2]) * t)
            pg.draw.line(grad, (r, g, b), (0, y), (w, y))
        _gradient_cache[key] = grad
    surface.blit(_gradient_cache[key], (0, 0))


def invalidate_cache():
    _gradient_cache.clear()


def glass_panel(surface, rect, alpha=PANEL_ALPHA, border=ACCENT_DIM,
                border_w=1, radius=8, fill=None):
    if fill is None:
        fill = PANEL
    panel = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
    pg.draw.rect(panel, (*fill[:3], alpha), (0, 0, rect.width, rect.height),
                 border_radius=radius)
    surface.blit(panel, rect.topleft)
    if border_w > 0:
        pg.draw.rect(surface, border, rect, border_w, border_radius=radius)


def glow_rect(surface, rect, color=ACCENT_GLOW, width=1, radius=8):
    for i in range(3, 0, -1):
        alpha = int(30 / i)
        expanded = rect.inflate(i * 4, i * 4)
        s = pg.Surface((expanded.width, expanded.height), pg.SRCALPHA)
        pg.draw.rect(s, (*color[:3], alpha), (0, 0, expanded.width, expanded.height),
                     width + i, border_radius=radius + i)
        surface.blit(s, expanded.topleft)
    pg.draw.rect(surface, color[:3], rect, width, border_radius=radius)


def button(surface, rect, label, size=16, hovered=False, active=False,
           accent=ACCENT, idle_fill=None):
    if idle_fill is None:
        idle_fill = (22, 30, 52)
    if active:
        fill, brd, tc = (0, 160, 155), accent, (10, 10, 10)
    elif hovered:
        fill, brd, tc = (32, 44, 72), accent, TEXT_BRIGHT
    else:
        fill, brd, tc = idle_fill, ACCENT_DIM, TEXT
    glass_panel(surface, rect, alpha=210, border=brd, fill=fill, radius=6)
    f = font(size)
    ts = f.render(str(label), True, tc)
    tr = ts.get_rect(center=rect.center)
    surface.blit(ts, tr)
    return rect


def text(surface, txt, x, y, size=16, color=TEXT, center=False):
    f = font(size)
    ts = f.render(str(txt), True, color)
    tr = ts.get_rect(center=(int(x), int(y))) if center else ts.get_rect(topleft=(int(x), int(y)))
    surface.blit(ts, tr)
    return tr


def unit_circle(surface, cx, cy, count, color, radius=13):
    dark = darken(color, 0.4)
    pg.draw.circle(surface, dark, (int(cx), int(cy)), radius)
    pg.draw.circle(surface, color[:3], (int(cx), int(cy)), radius, 2)
    f = font(max(8, int(radius * 1.1)))
    ts = f.render(str(count), True, TEXT_BRIGHT)
    tr = ts.get_rect(center=(int(cx), int(cy)))
    surface.blit(ts, tr)


def darken(color, factor=0.4):
    return tuple(max(0, int(c * factor)) for c in color[:3])


def lighten(color, amount=50):
    return tuple(min(255, c + amount) for c in color[:3])
