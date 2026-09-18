"""Constantes globales. Aucune dépendance à pygame : importable par les tests."""

W, H = 960, 600
FPS = 60
MAX_DT = 1 / 30

ARENA_X, ARENA_Y, ARENA_W, ARENA_H = 30, 30, 900, 540
DOOR_X, DOOR_Y, DOOR_W, DOOR_H = 430, 20, 100, 24

PLAYER_START = (W / 2, ARENA_Y + ARENA_H - 50)
BOSS_EVERY = 5
SPAWN_TIME = 0.6          # durée d'apparition des ennemis (inoffensifs)
COIN_MAGNET = 90

SAVE_KEY = "archer-quest-save-v1"

# Couleurs
GOLD = (255, 215, 94)
GOLD_DARK = (163, 102, 10)
RED = (255, 88, 88)
WHITE = (255, 255, 255)
TEXT = (232, 232, 255)
MUTED = (183, 183, 214)
PLAYER_COL = (94, 200, 255)
PLAYER_DARK = (26, 90, 134)
ARROW_COL = (255, 233, 173)
BG = (5, 5, 8)

PALETTES = [
    {"name": "Forêt", "floor": ((37, 66, 43), (44, 79, 51)), "wall": (14, 27, 16), "accent": (126, 224, 138)},
    {"name": "Caverne", "floor": ((51, 42, 68), (60, 51, 80)), "wall": (21, 15, 34), "accent": (180, 140, 255)},
    {"name": "Désert", "floor": ((74, 58, 35), (87, 69, 43)), "wall": (34, 26, 14), "accent": (255, 206, 107)},
    {"name": "Glacier", "floor": ((35, 58, 74), (42, 69, 87)), "wall": (14, 26, 34), "accent": (127, 212, 255)},
]


def palette_index(room: int) -> int:
    return ((room - 1) // BOSS_EVERY) % len(PALETTES)


def palette(room: int) -> dict:
    return PALETTES[palette_index(room)]
