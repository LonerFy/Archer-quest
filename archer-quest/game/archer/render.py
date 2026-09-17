"""Rendu pygame : monde, HUD, écrans et icônes vectorielles (aucune image externe)."""
import math

import pygame

from . import layout as L
from .config import (W, H, ARENA_X, ARENA_Y, ARENA_W, ARENA_H, DOOR_X, DOOR_Y, DOOR_W, DOOR_H,
                     GOLD, GOLD_DARK, RED, WHITE, TEXT, MUTED, PLAYER_COL, PLAYER_DARK, ARROW_COL,
                     BG, palette, palette_index, SPAWN_TIME)


def lerp_col(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def wrap(text, font, width):
    lines, cur = [], ""
    for word in text.split():
        test = f"{cur} {word}".strip()
        if font.size(test)[0] <= width:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Renderer:
    def __init__(self):
        f = lambda s: pygame.font.Font(None, s)
        self.font_s, self.font_m, self.font_l = f(20), f(26), f(34)
        self.font_xl, self.font_title = f(64), f(96)
        self.layer = pygame.Surface((W, H))
        self.dim = pygame.Surface((W, H), pygame.SRCALPHA)
        self.dim.fill((5, 5, 10, 215))
        self.fade = pygame.Surface((W, H), pygame.SRCALPHA)
        self._arena_cache = {}
        self._shadow_cache = {}
        self._text_cache = {}

    # ------------------------------------------------------------------ utilitaires
    def _render(self, txt, font, color):
        key = (txt, id(font), color)
        img = self._text_cache.get(key)
        if img is None:
            if len(self._text_cache) > 400:
                self._text_cache.clear()
            img = self._text_cache[key] = font.render(txt, True, color)
        return img

    def text(self, surf, txt, font, color, pos, anchor="center", shadow=True):
        img = self._render(txt, font, color)
        rect = img.get_rect(**{anchor: pos})
        if shadow:
            surf.blit(self._render(txt, font, (0, 0, 0)), rect.move(0, 2))
        surf.blit(img, rect)
        return rect

    def button(self, surf, rect, label, enabled=True, hover=False, font=None):
        font = font or self.font_l
        top, bottom = ((255, 226, 122), (255, 178, 56)) if enabled else ((110, 110, 130), (80, 80, 96))
        if hover and enabled:
            top, bottom = (255, 238, 160), (255, 196, 90)
        shadow_col = GOLD_DARK if enabled else (50, 50, 60)
        pygame.draw.rect(surf, shadow_col, rect.move(0, 5), border_radius=14)
        pygame.draw.rect(surf, bottom, rect, border_radius=14)
        upper = pygame.Rect(rect.x, rect.y, rect.w, rect.h // 2)
        pygame.draw.rect(surf, top, upper, border_top_left_radius=14, border_top_right_radius=14)
        self.text(surf, label, font, (58, 36, 0) if enabled else (40, 40, 50), rect.center, shadow=False)

    def _shadow(self, r):
        r = int(r)
        s = self._shadow_cache.get(r)
        if s is None:
            s = pygame.Surface((int(r * 1.8), int(r * 0.7)), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 0, 90), s.get_rect())
            self._shadow_cache[r] = s
        return s

    def _arena(self, room):
        idx = palette_index(room)
        surf = self._arena_cache.get(idx)
        if surf:
            return surf
        pal = palette(room)
        surf = pygame.Surface((W, H))
        surf.fill(BG)
        for y in range(ARENA_H):
            col = lerp_col(pal["floor"][0], pal["floor"][1], y / ARENA_H)
            pygame.draw.line(surf, col, (ARENA_X, ARENA_Y + y), (ARENA_X + ARENA_W, ARENA_Y + y))
        grid = lerp_col(pal["floor"][0], WHITE, 0.05)
        for x in range(ARENA_X, ARENA_X + ARENA_W + 1, 40):
            pygame.draw.line(surf, grid, (x, ARENA_Y), (x, ARENA_Y + ARENA_H))
        for y in range(ARENA_Y, ARENA_Y + ARENA_H + 1, 40):
            pygame.draw.line(surf, grid, (ARENA_X, y), (ARENA_X + ARENA_W, y))
        pygame.draw.rect(surf, pal["wall"], (ARENA_X - 7, ARENA_Y - 7, ARENA_W + 14, ARENA_H + 14), 14)
        inner = lerp_col(pal["floor"][0], pal["accent"], 0.5)
        pygame.draw.rect(surf, inner, (ARENA_X + 7, ARENA_Y + 7, ARENA_W - 14, ARENA_H - 14), 2)
        self._arena_cache[idx] = surf
        return surf

    # ------------------------------------------------------------------ monde
    def draw_world(self, screen, world, t, joystick=None):
        s = self.layer
        s.blit(self._arena(world.room), (0, 0))
        pal = palette(world.room)

        if world.door_open:
            pulse = 0.6 + math.sin(t * 5.5) * 0.4
            pygame.draw.rect(s, lerp_col(pal["wall"], pal["accent"], 0.4 + pulse * 0.5),
                             (DOOR_X, DOOR_Y, DOOR_W, DOOR_H + 14))
            self.text(s, "SORTIE", self.font_s, WHITE, (DOOR_X + DOOR_W // 2, DOOR_Y + DOOR_H + 30))
        else:
            pygame.draw.rect(s, pal["wall"], (DOOR_X, DOOR_Y - 6, DOOR_W, DOOR_H + 6))

        for c in world.coins:
            pygame.draw.circle(s, GOLD, (c.x, c.y), 5)
            pygame.draw.circle(s, GOLD_DARK, (c.x, c.y), 5, 2)

        for pr in world.e_proj:
            pygame.draw.circle(s, (140, 30, 30), (pr.x, pr.y), pr.r + 3)
            pygame.draw.circle(s, (255, 91, 91), (pr.x, pr.y), pr.r)
            pygame.draw.circle(s, (255, 200, 200), (pr.x, pr.y), max(1, pr.r - 3))

        for pr in world.p_proj:
            a = math.atan2(pr.vy, pr.vx)
            ca, sa = math.cos(a), math.sin(a)
            tail = (pr.x - ca * 9, pr.y - sa * 9)
            tip = (pr.x + ca * 9, pr.y + sa * 9)
            pygame.draw.line(s, ARROW_COL, tail, tip, 3)
            head = [(pr.x + ca * 12, pr.y + sa * 12),
                    (pr.x + ca * 5 - sa * 4, pr.y + sa * 5 + ca * 4),
                    (pr.x + ca * 5 + sa * 4, pr.y + sa * 5 - ca * 4)]
            pygame.draw.polygon(s, GOLD, head)

        for e in world.enemies:
            self._draw_enemy(s, e, t)

        self._draw_player(s, world.player, t)

        for pt in world.particles:
            r = pt.r * max(0.0, pt.life / pt.max_life)
            if r >= 0.5:
                pygame.draw.circle(s, pt.color, (pt.x, pt.y), r)

        for fl in world.floaters:
            img = (self.font_l if fl.big else self.font_m).render(fl.text, True, fl.color)
            img.set_alpha(int(255 * max(0.0, min(1.0, fl.life / 0.8))))
            s.blit(img, img.get_rect(center=(fl.x, fl.y)))

        if joystick and joystick.pointer:
            self._draw_joystick(s, joystick)

        ox = oy = 0
        if world.shake_t > 0:
            ox = world.rng.uniform(-world.shake_mag, world.shake_mag)
            oy = world.rng.uniform(-world.shake_mag, world.shake_mag)
        screen.fill(BG)
        screen.blit(s, (ox, oy))

    def _draw_player(self, s, p, t):
        sh = self._shadow(p.r)
        s.blit(sh, sh.get_rect(center=(p.x, p.y + p.r * 0.8)))
        body = WHITE if p.hit_flash > 0 else PLAYER_COL
        pygame.draw.circle(s, body, (p.x, p.y), p.r)
        pygame.draw.circle(s, PLAYER_DARK, (p.x, p.y), p.r, 2)
        fx, fy = math.cos(p.facing), math.sin(p.facing)
        # arc = l'arc du personnage, perpendiculaire à la visée
        bow_c = (p.x + fx * (p.r - 2), p.y + fy * (p.r - 2))
        px, py = -fy, fx
        pygame.draw.line(s, (120, 70, 20), (bow_c[0] + px * 11 - fx * 4, bow_c[1] + py * 11 - fy * 4),
                         (bow_c[0] + fx * 5, bow_c[1] + fy * 5), 3)
        pygame.draw.line(s, (120, 70, 20), (bow_c[0] - px * 11 - fx * 4, bow_c[1] - py * 11 - fy * 4),
                         (bow_c[0] + fx * 5, bow_c[1] + fy * 5), 3)
        pygame.draw.line(s, GOLD, (p.x, p.y), (p.x + fx * (p.r + 9), p.y + fy * (p.r + 9)), 3)
        if p.invuln > 0 and int(t * 12.5) % 2 == 0:
            pygame.draw.circle(s, (220, 220, 230), (p.x, p.y), p.r + 4, 2)

    def _draw_enemy(self, s, e, t):
        scale = 1.0
        if e.spawn_t > 0:
            k = 1 - e.spawn_t / SPAWN_TIME
            scale = 0.3 + 0.7 * k
            pygame.draw.circle(s, e.color, (e.x, e.y), e.r + 10 * (1 - k), 2)
        r = e.r * scale
        sh = self._shadow(r)
        s.blit(sh, sh.get_rect(center=(e.x, e.y + r * 0.8)))

        if e.kind == "dasher" and e.state == "windup" and int(t * 16) % 2 == 0:
            end = (e.x + e.dir_x * 150, e.y + e.dir_y * 150)
            pygame.draw.line(s, (255, 90, 90), (e.x, e.y), end, 2)

        color = WHITE if e.hit_flash > 0 else e.color
        if e.kind == "dasher":
            pts = [(e.x, e.y - r * 1.25), (e.x + r * 1.1, e.y), (e.x, e.y + r * 1.25), (e.x - r * 1.1, e.y)]
            pygame.draw.polygon(s, color, pts)
            pygame.draw.polygon(s, e.dark, pts, 3)
        elif e.kind == "tank":
            rect = pygame.Rect(0, 0, r * 2, r * 2)
            rect.center = (e.x, e.y)
            pygame.draw.rect(s, color, rect, border_radius=int(r * 0.45))
            pygame.draw.rect(s, e.dark, rect, 3, border_radius=int(r * 0.45))
        else:
            pygame.draw.circle(s, color, (e.x, e.y), r)
            pygame.draw.circle(s, e.dark, (e.x, e.y), r, 3)

        eye = (26, 26, 26)
        pygame.draw.circle(s, eye, (e.x - r * 0.32, e.y - r * 0.15), max(1, r * 0.14))
        pygame.draw.circle(s, eye, (e.x + r * 0.32, e.y - r * 0.15), max(1, r * 0.14))

        if e.boss:
            cx, cy, w = e.x, e.y - r - 14, r * 0.9
            crown = [(cx - w, cy + 8), (cx - w, cy - 6), (cx - w / 2, cy + 2), (cx, cy - 10),
                     (cx + w / 2, cy + 2), (cx + w, cy - 6), (cx + w, cy + 8)]
            pygame.draw.polygon(s, GOLD if e.phase == 1 else RED, crown)
            pygame.draw.polygon(s, GOLD_DARK, crown, 2)

        if e.spawn_t <= 0:
            w = e.r * 2.2
            y = e.y - e.r - (26 if e.boss else 12)
            pygame.draw.rect(s, (0, 0, 0), (e.x - w / 2, y, w, 5))
            frac = max(0.0, min(1.0, e.hp / e.max_hp))
            pygame.draw.rect(s, (255, 46, 46) if e.boss else (126, 224, 138), (e.x - w / 2, y, w * frac, 5))

    def _draw_joystick(self, s, joy):
        sx, sy = joy.start
        pygame.draw.circle(s, (230, 230, 240), (sx, sy), joy.MAXR, 2)
        dx, dy = joy.cur[0] - sx, joy.cur[1] - sy
        d = math.hypot(dx, dy)
        if d > joy.MAXR:
            dx, dy = dx / d * joy.MAXR, dy / d * joy.MAXR
        pygame.draw.circle(s, (230, 230, 240), (sx + dx, sy + dy), 16)

    # ------------------------------------------------------------------ HUD
    def draw_hud(self, s, world, muted, best_room):
        p = world.player
        r = L.HP_BAR
        pygame.draw.rect(s, (0, 0, 0), r.inflate(4, 4), border_radius=12)
        frac = max(0.0, p.hp / p.max_hp)
        if frac > 0:
            fill = pygame.Rect(r.x, r.y, max(r.h, int(r.w * frac)), r.h)
            col = (255, 70, 70) if frac > 0.3 or int(world.elapsed * 4) % 2 else (255, 150, 150)
            pygame.draw.rect(s, col, fill, border_radius=10)
        self.text(s, f"{math.ceil(p.hp)}/{round(p.max_hp)}", self.font_s, WHITE, r.center)

        g = L.GOLD_PILL
        pygame.draw.rect(s, (0, 0, 0), g, border_radius=13)
        pygame.draw.rect(s, (70, 70, 90), g, 2, border_radius=13)
        pygame.draw.circle(s, GOLD, (g.x + 16, g.centery), 7)
        pygame.draw.circle(s, GOLD_DARK, (g.x + 16, g.centery), 7, 2)
        self.text(s, str(world.gold), self.font_m, WHITE, (g.x + 30, g.centery), anchor="midleft")

        label = f"BOSS - SALLE {world.room}" if world.is_boss_room else f"SALLE {world.room}"
        img = self.font_m.render(label, True, GOLD)
        pill = img.get_rect(center=(W // 2, 23)).inflate(28, 10)
        pygame.draw.rect(s, (0, 0, 0), pill, border_radius=14)
        pygame.draw.rect(s, (70, 70, 90), pill, 2, border_radius=14)
        s.blit(img, img.get_rect(center=pill.center))

        for rect in (L.PAUSE_BTN, L.SOUND_BTN):
            pygame.draw.rect(s, (0, 0, 0), rect, border_radius=8)
            pygame.draw.rect(s, (70, 70, 90), rect, 2, border_radius=8)
        pb = L.PAUSE_BTN
        pygame.draw.rect(s, WHITE, (pb.centerx - 7, pb.y + 8, 5, 14))
        pygame.draw.rect(s, WHITE, (pb.centerx + 2, pb.y + 8, 5, 14))
        self._speaker(s, L.SOUND_BTN, muted)

        if world.room == 1 and world.elapsed < 6:
            self.text(s, "Bougez pour esquiver - arrêtez-vous pour tirer", self.font_s, MUTED, (W // 2, H - 16))

    def _speaker(self, s, rect, muted):
        cx, cy = rect.centerx - 4, rect.centery
        pygame.draw.polygon(s, WHITE, [(cx - 9, cy - 4), (cx - 4, cy - 4), (cx + 2, cy - 9),
                                       (cx + 2, cy + 9), (cx - 4, cy + 4), (cx - 9, cy + 4)])
        if muted:
            pygame.draw.line(s, RED, (cx + 6, cy - 5), (cx + 14, cy + 5), 3)
            pygame.draw.line(s, RED, (cx + 14, cy - 5), (cx + 6, cy + 5), 3)
        else:
            pygame.draw.arc(s, WHITE, (cx + 1, cy - 7, 10, 14), -1.1, 1.1, 2)
            pygame.draw.arc(s, WHITE, (cx + 3, cy - 11, 14, 22), -1.1, 1.1, 2)

    # ------------------------------------------------------------------ écrans
    def draw_fade(self, s, alpha):
        self.fade.fill((5, 5, 10, int(255 * max(0.0, min(1.0, alpha)))))
        s.blit(self.fade, (0, 0))

    def _title(self, s, txt, color, y, font=None):
        font = font or self.font_xl
        img = font.render(txt, True, color)
        dark = font.render(txt, True, lerp_col(color, (0, 0, 0), 0.6))
        rect = img.get_rect(center=(W // 2, y))
        s.blit(dark, rect.move(0, 4))
        s.blit(img, rect)

    def draw_title(self, s, best_room, mouse):
        s.blit(self.dim, (0, 0))
        self._title(s, "ARCHER QUEST", GOLD, 150, self.font_title)
        lines = [
            "Déplacement : ZQSD / WASD / flèches, ou maintenez et glissez (souris, doigt).",
            "Arrêtez-vous pour tirer automatiquement sur l'ennemi le plus proche.",
            "Nettoyez chaque salle, choisissez une amélioration, battez le boss toutes les 5 salles.",
        ]
        for i, line in enumerate(lines):
            self.text(s, line, self.font_m, TEXT, (W // 2, 245 + i * 34))
        self.text(s, "P / Échap : pause     M : son", self.font_s, MUTED, (W // 2, 360))
        if best_room:
            self.text(s, f"Record : salle {best_room}", self.font_m, GOLD, (W // 2, 520))
        self.button(s, L.PLAY_BTN, "JOUER", hover=L.PLAY_BTN.collidepoint(mouse))

    def draw_pause(self, s, mouse):
        s.blit(self.dim, (0, 0))
        self._title(s, "PAUSE", GOLD, 190)
        self.button(s, L.RESUME_BTN, "REPRENDRE", hover=L.RESUME_BTN.collidepoint(mouse))
        self.button(s, L.MENU_BTN, "MENU", hover=L.MENU_BTN.collidepoint(mouse))

    def draw_upgrade(self, s, world, choices, cost, mouse):
        s.blit(self.dim, (0, 0))
        self._title(s, "SALLE NETTOYÉE !", GOLD, 110, self.font_xl)
        self.text(s, "Choisissez une amélioration (clic ou touches 1, 2, 3)", self.font_m, MUTED, (W // 2, 165))
        for i, (u, rect) in enumerate(zip(choices, L.card_rects(len(choices)))):
            hover = rect.collidepoint(mouse)
            r = rect.move(0, -6) if hover else rect
            pygame.draw.rect(s, (28, 28, 50), r, border_radius=16)
            border = GOLD if (u.rare or hover) else (76, 76, 122)
            pygame.draw.rect(s, border, r, 3, border_radius=16)
            if u.rare:
                self.text(s, "RARE", self.font_s, GOLD, (r.centerx, r.y + 18), shadow=False)
            draw_icon(s, u.id, (r.centerx, r.y + 78), 34)
            self.text(s, u.name, self.font_l, GOLD if u.rare else WHITE, (r.centerx, r.y + 138))
            for j, line in enumerate(wrap(u.desc, self.font_s, r.w - 24)):
                self.text(s, line, self.font_s, MUTED, (r.centerx, r.y + 172 + j * 20), shadow=False)
            self.text(s, str(i + 1), self.font_s, (110, 110, 150), (r.centerx, r.bottom - 16), shadow=False)
        can = world.gold >= cost
        self.button(s, L.REROLL_BTN, f"RELANCER (R) : {cost} or", enabled=can,
                    hover=L.REROLL_BTN.collidepoint(mouse), font=self.font_m)
        self.text(s, f"Or : {world.gold}", self.font_m, GOLD, (W // 2, 572))

    def draw_gameover(self, s, world, best_room, new_record, mouse):
        s.blit(self.dim, (0, 0))
        self._title(s, "MORT", RED, 130, self.font_title)
        minutes, seconds = divmod(int(world.elapsed), 60)
        stats = [("Salle atteinte", world.room), ("Ennemis vaincus", world.kills),
                 ("Or récolté", world.gold), ("Temps", f"{minutes}:{seconds:02d}"),
                 ("Record", f"salle {best_room}")]
        for i, (k, v) in enumerate(stats):
            y = 220 + i * 36
            self.text(s, f"{k} :", self.font_m, TEXT, (W // 2 - 10, y), anchor="midright")
            self.text(s, str(v), self.font_m, GOLD, (W // 2 + 10, y), anchor="midleft")
        if new_record:
            self.text(s, "NOUVEAU RECORD !", self.font_l, GOLD, (W // 2, 410))
        self.button(s, L.RETRY_BTN, "RECOMMENCER", hover=L.RETRY_BTN.collidepoint(mouse))


# ---------------------------------------------------------------------- icônes
def draw_icon(s, uid, center, size):
    cx, cy = center
    k = size / 34
    P = lambda x, y: (cx + x * k, cy + y * k)
    if uid == "dmg":
        pygame.draw.line(s, (220, 220, 235), P(-18, 18), P(16, -16), max(1, int(6 * k)))
        pygame.draw.line(s, GOLD_DARK, P(-12, 4), P(-4, 12), max(1, int(5 * k)))
        pygame.draw.line(s, GOLD, P(-22, 22), P(-15, 15), max(1, int(6 * k)))
    elif uid == "atkspd":
        pygame.draw.polygon(s, GOLD, [P(4, -26), P(-14, 4), P(-1, 4), P(-6, 26), P(14, -6), P(1, -6)])
    elif uid in ("hp", "lifesteal"):
        col = (255, 70, 90) if uid == "hp" else (160, 20, 40)
        if uid == "hp":
            pygame.draw.circle(s, col, P(-9, -6), 11 * k)
            pygame.draw.circle(s, col, P(9, -6), 11 * k)
            pygame.draw.polygon(s, col, [P(-19, -1), P(19, -1), P(0, 22)])
        else:
            pygame.draw.circle(s, col, P(0, 8), 14 * k)
            pygame.draw.polygon(s, col, [P(-13, 3), P(13, 3), P(0, -24)])
            pygame.draw.circle(s, (255, 120, 140), P(-5, 8), 4 * k)
    elif uid == "spd":
        for off in (-12, 4):
            pygame.draw.lines(s, (126, 224, 138), False, [P(off, -16), P(off + 14, 0), P(off, 16)], max(1, int(6 * k)))
    elif uid == "crit":
        for rad, col in ((24, (255, 91, 91)), (16, WHITE), (8, (255, 91, 91))):
            pygame.draw.circle(s, col, P(0, 0), rad * k)
    elif uid == "heal":
        pygame.draw.rect(s, (126, 224, 138), (*P(-7, -22), 14 * k, 44 * k), border_radius=3)
        pygame.draw.rect(s, (126, 224, 138), (*P(-22, -7), 44 * k, 14 * k), border_radius=3)
    elif uid == "gold":
        for i, dy in enumerate((12, 2, -8)):
            pygame.draw.ellipse(s, GOLD, (*P(-18, dy - 6), 36 * k, 14 * k))
            pygame.draw.ellipse(s, GOLD_DARK, (*P(-18, dy - 6), 36 * k, 14 * k), 2)
    elif uid in ("multishot", "pierce", "back"):
        angles = {"multishot": (-0.45, 0, 0.45), "pierce": (0,), "back": (0, math.pi)}[uid]
        if uid == "pierce":
            pygame.draw.circle(s, (255, 91, 91), P(0, 0), 11 * k)
        for a in angles:
            ca, sa = math.cos(a - math.pi / 2), math.sin(a - math.pi / 2)
            start, end = P(-ca * 4, -sa * 4) if uid == "back" else P(-ca * 20, -sa * 20), P(ca * 24, sa * 24)
            pygame.draw.line(s, ARROW_COL, start, end, max(1, int(4 * k)))
            tip = P(ca * 28, sa * 28)
            left = P(ca * 18 - sa * 6, sa * 18 + ca * 6)
            right = P(ca * 18 + sa * 6, sa * 18 - ca * 6)
            pygame.draw.polygon(s, GOLD, [tip, left, right])
    else:
        pygame.draw.circle(s, GOLD, P(0, 0), 20 * k)
