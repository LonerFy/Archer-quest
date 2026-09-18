"""Positions des éléments d'interface (partagées par le rendu et la gestion des clics)."""
import pygame

from .config import W

HP_BAR = pygame.Rect(14, 12, 240, 22)
GOLD_PILL = pygame.Rect(266, 10, 104, 26)
PAUSE_BTN = pygame.Rect(W - 100, 8, 40, 30)
SOUND_BTN = pygame.Rect(W - 54, 8, 40, 30)


def _centered(w, h, cy):
    r = pygame.Rect(0, 0, w, h)
    r.center = (W // 2, cy)
    return r


PLAY_BTN = _centered(230, 62, 440)
RETRY_BTN = _centered(260, 62, 470)
RESUME_BTN = _centered(260, 58, 300)
MENU_BTN = _centered(260, 58, 380)
REROLL_BTN = _centered(300, 50, 520)


def card_rects(n):
    w, h, gap, top = 210, 250, 24, 205
    x0 = (W - (n * w + (n - 1) * gap)) // 2
    return [pygame.Rect(x0 + i * (w + gap), top, w, h) for i in range(n)]
