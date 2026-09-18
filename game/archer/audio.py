"""Sons synthétisés à la volée (aucun fichier audio à héberger)."""
import array
import math

import pygame

# nom -> liste de (fréquence, durée, forme, volume, fréquence finale, délai)
SPEC = {
    "shoot": [(880, .08, "triangle", .22, 660, 0)],
    "hit": [(160, .09, "square", .14, 80, 0)],
    "crit": [(1200, .12, "saw", .18, 500, 0)],
    "enemy_die": [(300, .16, "saw", .2, 60, 0)],
    "hurt": [(120, .18, "square", .22, 50, 0)],
    "levelup": [(660, .1, "sine", .3, 880, 0), (990, .14, "sine", .3, 1320, .09)],
    "door": [(220, .3, "sine", .3, 440, 0)],
    "gold": [(1400, .05, "sine", .12, 1800, 0)],
    "boss_phase": [(90, .5, "saw", .3, 40, 0)],
    "death": [(400, .6, "square", .2, 60, 0)],
    "deny": [(150, .12, "square", .18, 140, 0)],
    "select": [(520, .08, "triangle", .25, 780, 0)],
}


def _wave(kind, phase):
    if kind == "sine":
        return math.sin(phase)
    if kind == "square":
        return 1.0 if math.sin(phase) >= 0 else -1.0
    if kind == "triangle":
        return 2 / math.pi * math.asin(math.sin(phase))
    return ((phase / math.tau) % 1.0) * 2 - 1  # saw


class Audio:
    def __init__(self):
        self.muted = False
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            rate, size, channels = pygame.mixer.get_init()
            for name, tones in SPEC.items():
                self.sounds[name] = self._build(tones, rate, size, channels)
        except Exception as exc:  # pas d'audio : le jeu reste jouable
            print("Audio désactivé :", exc)
            self.sounds = {}

    @staticmethod
    def _build(tones, rate, size, channels):
        total = int(max(delay + dur for _, dur, _, _, _, delay in tones) * rate) + 1
        buf = [0.0] * total
        for f0, dur, kind, vol, f1, delay in tones:
            start, n = int(delay * rate), int(dur * rate)
            phase = 0.0
            for i in range(n):
                t = i / n
                freq = f0 * (f1 / f0) ** t
                phase += math.tau * freq / rate
                env = vol * (0.001 ** t) * min(1.0, i / (0.003 * rate))
                buf[start + i] += _wave(kind, phase) * env
        if size == 32:
            fmt, scale, offset = "f", 1.0, 0.0
        elif size == -32:
            fmt, scale, offset = "i", 2**31 - 1, 0.0
        elif size == 16:
            fmt, scale, offset = "H", 32767, 32768
        else:
            fmt, scale, offset = "h", 32767, 0
        samples = array.array(fmt)
        for v in buf:
            s = max(-1.0, min(1.0, v)) * scale + offset
            s = s if fmt == "f" else int(s)
            for _ in range(channels):
                samples.append(s)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name):
        if not self.muted and name in self.sounds:
            self.sounds[name].play()
