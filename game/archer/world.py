"""Simulation du jeu : logique pure, déterministe avec une graine, testable sans pygame.

L'application lit `world.events` (noms de sons) après chaque update puis les vide.
"""
import math
import random

from .config import (ARENA_X, ARENA_Y, ARENA_W, ARENA_H, DOOR_X, DOOR_Y, DOOR_W, DOOR_H,
                     PLAYER_START, BOSS_EVERY, COIN_MAGNET, GOLD, RED, WHITE)
from .entities import Player, Projectile, Particle, Floater, Coin, make_enemy
from .upgrades import roll_upgrades

ARROW_SPEED = 520
ENEMY_SHOT_SPEED = 230


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def out_of_arena(x, y, margin=20):
    return (x < ARENA_X - margin or x > ARENA_X + ARENA_W + margin
            or y < ARENA_Y - margin or y > ARENA_Y + ARENA_H + margin)


class World:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.reset()

    # ------------------------------------------------------------------ cycle de vie
    def reset(self):
        self.room = 1
        self.gold = 0
        self.kills = 0
        self.elapsed = 0.0
        self.player = Player()
        self.upgrade_counts = {}
        self.particles = []
        self.floaters = []
        self.events = []
        self.shake_mag = 0.0
        self.shake_t = 0.0
        self.dead = False
        self.spawn_room()

    @property
    def is_boss_room(self):
        return self.room % BOSS_EVERY == 0

    def spawn_room(self):
        self.enemies, self.p_proj, self.e_proj, self.coins = [], [], [], []
        self.door_open = False
        self.exited = False
        p = self.player
        p.x, p.y = PLAYER_START
        p.facing = -math.pi / 2
        p.shot_timer = 0.0
        p.invuln = 0.0

        if self.is_boss_room:
            self.enemies.append(make_enemy("boss", ARENA_X + ARENA_W / 2, 150, self.room, self.rng))
            return

        count = min(3 + self.room // 2, 9)
        for _ in range(count):
            kind = self._pick_kind()
            for _try in range(30):
                x = self.rng.uniform(ARENA_X + 40, ARENA_X + ARENA_W - 40)
                y = self.rng.uniform(ARENA_Y + 40, ARENA_Y + ARENA_H * 0.55)
                if dist(x, y, p.x, p.y) >= 180 and all(dist(x, y, e.x, e.y) >= e.r + 30 for e in self.enemies):
                    break
            self.enemies.append(make_enemy(kind, x, y, self.room, self.rng))

    def _pick_kind(self):
        kinds, weights = ["chaser", "shooter", "tank"], [50, 30, 20]
        if self.room >= 3:
            kinds.append("dasher")
            weights.append(18)
        return self.rng.choices(kinds, weights)[0]

    def roll_choices(self):
        return roll_upgrades(self, self.rng)

    def apply_upgrade(self, upgrade):
        upgrade.apply(self)
        self.upgrade_counts[upgrade.id] = self.upgrade_counts.get(upgrade.id, 0) + 1

    def next_room(self):
        self.room += 1
        self.spawn_room()

    # ------------------------------------------------------------------ helpers
    def add_shake(self, mag, t):
        self.shake_mag = max(self.shake_mag, mag)
        self.shake_t = max(self.shake_t, t)

    def spawn_particles(self, x, y, color, n=8, speed=140):
        for _ in range(n):
            a = self.rng.uniform(0, math.tau)
            s = speed * self.rng.random()
            life = 0.4 + self.rng.random() * 0.3
            self.particles.append(Particle(x, y, math.cos(a) * s, math.sin(a) * s,
                                           life, 0.7, color, 2 + self.rng.random() * 2))

    def nearest_enemy(self):
        p = self.player
        active = [e for e in self.enemies if e.active]
        return min(active, key=lambda e: dist(e.x, e.y, p.x, p.y), default=None)

    # ------------------------------------------------------------------ update
    def update(self, dt, move=(0.0, 0.0, 0.0)):
        if self.dead or self.exited:
            return
        self.elapsed += dt
        self._update_player(dt, move)
        self._update_enemies(dt)
        self._separate_enemies()
        self._update_player_projectiles(dt)
        self._update_enemy_projectiles(dt)
        self._update_coins(dt)
        self._update_fx(dt)

        p = self.player
        if not self.door_open and not self.enemies:
            self.door_open = True
            self.events.append("door")
        if (self.door_open and p.y < DOOR_Y + DOOR_H + p.r
                and DOOR_X - 10 < p.x < DOOR_X + DOOR_W + 10):
            self.gold += sum(c.val for c in self.coins)
            self.coins.clear()
            self.exited = True
        if p.hp <= 0:
            p.hp = 0
            self.dead = True
            self.events.append("death")

        if self.shake_t > 0:
            self.shake_t -= dt
            if self.shake_t <= 0:
                self.shake_mag = 0.0

    def _update_player(self, dt, move):
        p = self.player
        mx, my, mag = move
        p.moving = mag > 0
        if p.moving:
            sp = p.speed * p.speed_mult * mag
            p.x = clamp(p.x + mx * sp * dt, ARENA_X + p.r, ARENA_X + ARENA_W - p.r)
            p.y = clamp(p.y + my * sp * dt, ARENA_Y + p.r, ARENA_Y + ARENA_H - p.r)
            p.facing = math.atan2(my, mx)
        p.shot_timer += dt
        if not p.moving and p.shot_timer >= p.fire_rate:
            target = self.nearest_enemy()
            if target:
                self._player_shoot(target)
                p.shot_timer = 0.0
        p.invuln = max(0.0, p.invuln - dt)
        p.hit_flash = max(0.0, p.hit_flash - dt)

    def _player_shoot(self, target):
        p = self.player
        base = math.atan2(target.y - p.y, target.x - p.x)
        p.facing = base
        n = p.arrows
        spread = math.radians(min(38, 10 * (n - 1)))
        angles = [base + (0 if n == 1 else (i / (n - 1) - 0.5) * spread) for i in range(n)]
        if p.back_arrow:
            angles.append(base + math.pi)
        for a in angles:
            self.p_proj.append(Projectile(p.x + math.cos(a) * 18, p.y + math.sin(a) * 18,
                                          math.cos(a) * ARROW_SPEED, math.sin(a) * ARROW_SPEED,
                                          4, pierce_left=p.pierce))
        self.events.append("shoot")

    def _enemy_fire(self, e, angle, r=5):
        self.e_proj.append(Projectile(e.x, e.y, math.cos(angle) * ENEMY_SHOT_SPEED,
                                      math.sin(angle) * ENEMY_SHOT_SPEED, r, dmg=e.dmg))

    def _hurt_player(self, dmg, invuln):
        p = self.player
        if p.invuln > 0:
            return False
        p.hp -= dmg
        p.invuln = invuln
        p.hit_flash = 0.25
        self.add_shake(6, 0.18)
        self.events.append("hurt")
        self.spawn_particles(p.x, p.y, RED, 10, 150)
        return True

    def _step_toward(self, e, angle, speed, dt, sign=1):
        e.x += math.cos(angle) * speed * dt * sign
        e.y += math.sin(angle) * speed * dt * sign

    def _update_enemies(self, dt):
        p = self.player
        for e in self.enemies:
            e.hit_flash = max(0.0, e.hit_flash - dt)
            if e.spawn_t > 0:
                e.spawn_t -= dt
                continue
            d = dist(e.x, e.y, p.x, p.y)
            a = math.atan2(p.y - e.y, p.x - e.x)

            if e.kind in ("chaser", "tank"):
                if d > 24:
                    self._step_toward(e, a, e.speed, dt)

            elif e.kind == "shooter":
                if d < 190:
                    self._step_toward(e, a, e.speed, dt, -1)
                elif d > 260:
                    self._step_toward(e, a, e.speed, dt)
                e.shoot_cd -= dt
                if e.shoot_cd <= 0:
                    self._enemy_fire(e, a)
                    e.shoot_cd = 1.4

            elif e.kind == "dasher":
                e.timer -= dt
                if e.state == "idle":
                    self._step_toward(e, a, e.speed, dt)
                    if e.timer <= 0 and d < 340:
                        e.state, e.timer = "windup", 0.55
                        e.dir_x, e.dir_y = math.cos(a), math.sin(a)
                elif e.state == "windup":
                    if e.timer <= 0:
                        e.state, e.timer = "dash", 0.35
                elif e.state == "dash":
                    e.x += e.dir_x * 430 * dt
                    e.y += e.dir_y * 430 * dt
                    if e.timer <= 0:
                        e.state, e.timer = "idle", 1.6

            elif e.boss:
                if e.phase == 1 and e.hp <= e.max_hp * 0.5:
                    e.phase = 2
                    e.speed *= 1.25
                    self.events.append("boss_phase")
                    self.add_shake(8, 0.4)
                    self.floaters.append(Floater(e.x, e.y - e.r - 20, "ENRAGÉ !", RED, 1.2, big=True))
                if d > 70:
                    self._step_toward(e, a, e.speed, dt)
                e.shoot_cd -= dt
                if e.shoot_cd <= 0:
                    spread = 2 if e.phase == 2 else 1
                    for k in range(-spread, spread + 1):
                        self._enemy_fire(e, a + k * 0.24, r=6)
                    e.shoot_cd = 0.9 if e.phase == 2 else 1.15
                if e.phase == 2:
                    e.burst_cd -= dt
                    if e.burst_cd <= 0:
                        for k in range(14):
                            self._enemy_fire(e, k * math.tau / 14 + self.elapsed, r=6)
                        e.burst_cd = 2.6

            e.x = clamp(e.x, ARENA_X + e.r, ARENA_X + ARENA_W - e.r)
            e.y = clamp(e.y, ARENA_Y + e.r, ARENA_Y + ARENA_H - e.r)
            e.touch_cd = max(0.0, e.touch_cd - dt)
            if dist(e.x, e.y, p.x, p.y) < e.r + p.r and e.touch_cd <= 0:
                if self._hurt_player(e.dmg, 0.7):
                    e.touch_cd = 0.5

    def _separate_enemies(self):
        es = self.enemies
        for i in range(len(es)):
            a = es[i]
            for j in range(i + 1, len(es)):
                b = es[j]
                dx, dy = b.x - a.x, b.y - a.y
                d = math.hypot(dx, dy)
                min_d = a.r + b.r
                if 0 < d < min_d:
                    push = min_d - d
                    nx, ny = dx / d, dy / d
                    wa, wb = (0.0, 1.0) if a.boss else (1.0, 0.0) if b.boss else (0.5, 0.5)
                    a.x -= nx * push * wa
                    a.y -= ny * push * wa
                    b.x += nx * push * wb
                    b.y += ny * push * wb

    def _damage_enemy(self, e, dmg, crit):
        e.hp -= dmg
        e.hit_flash = 0.08
        self.floaters.append(Floater(e.x, e.y - e.r, f"{round(dmg)}{'!' if crit else ''}",
                                     GOLD if crit else WHITE, big=crit))
        self.spawn_particles(e.x, e.y, e.color, 5, 90)
        self.events.append("crit" if crit else "hit")
        if e.hp <= 0:
            self.kills += 1
            self.spawn_particles(e.x, e.y, e.color, 30 if e.boss else 18, 260 if e.boss else 220)
            self.events.append("enemy_die")
            self.add_shake(10 if e.boss else 3, 0.35 if e.boss else 0.12)
            drops = 25 if e.boss else self.rng.randint(3, 8)
            for _ in range(drops):
                self.coins.append(Coin(e.x + self.rng.uniform(-14, 14), e.y + self.rng.uniform(-14, 14)))
            p = self.player
            if p.lifesteal and p.hp > 0:
                healed = min(p.lifesteal, p.max_hp - p.hp)
                if healed > 0:
                    p.hp += healed
                    self.floaters.append(Floater(p.x, p.y - p.r - 6, f"+{round(healed)}", (126, 224, 138)))

    def _update_player_projectiles(self, dt):
        alive = []
        crit_chance = self.player.crit
        for pr in self.p_proj:
            pr.x += pr.vx * dt
            pr.y += pr.vy * dt
            if out_of_arena(pr.x, pr.y):
                continue
            keep = True
            for e in self.enemies:
                if not e.active or e in pr.hits:
                    continue
                if dist(pr.x, pr.y, e.x, e.y) < pr.r + e.r:
                    crit = self.rng.random() < crit_chance
                    self._damage_enemy(e, self.player.damage * (2 if crit else 1), crit)
                    pr.hits.add(e)
                    if pr.pierce_left <= 0:
                        keep = False
                    else:
                        pr.pierce_left -= 1
                    break
            if keep:
                alive.append(pr)
        self.p_proj = alive
        self.enemies = [e for e in self.enemies if e.hp > 0]

    def _update_enemy_projectiles(self, dt):
        p = self.player
        alive = []
        for pr in self.e_proj:
            pr.x += pr.vx * dt
            pr.y += pr.vy * dt
            if out_of_arena(pr.x, pr.y):
                continue
            if p.invuln <= 0 and dist(pr.x, pr.y, p.x, p.y) < pr.r + p.r:
                self._hurt_player(pr.dmg, 0.6)
                continue
            alive.append(pr)
        self.e_proj = alive

    def _update_coins(self, dt):
        p = self.player
        alive = []
        for c in self.coins:
            d = dist(c.x, c.y, p.x, p.y)
            if d < 20:
                self.gold += c.val
                self.events.append("gold")
                continue
            if self.door_open or d < COIN_MAGNET:  # salle vide : l'or vient tout seul
                a = math.atan2(p.y - c.y, p.x - c.x)
                c.vx, c.vy = math.cos(a) * 420, math.sin(a) * 420
            c.x += c.vx * dt
            c.y += c.vy * dt
            alive.append(c)
        self.coins = alive

    def _update_fx(self, dt):
        for pt in self.particles:
            pt.life -= dt
            pt.x += pt.vx * dt
            pt.y += pt.vy * dt
            pt.vx *= 0.92
            pt.vy *= 0.92
        self.particles = [pt for pt in self.particles if pt.life > 0]
        for f in self.floaters:
            f.life -= dt
            f.y += f.vy * dt
            f.vy *= 0.9
        self.floaters = [f for f in self.floaters if f.life > 0]
