"""Entités du jeu (données pures, sans pygame)."""
import math
from dataclasses import dataclass, field

from .config import PLAYER_START, SPAWN_TIME


@dataclass
class Player:
    x: float = PLAYER_START[0]
    y: float = PLAYER_START[1]
    r: float = 16.0
    speed: float = 230.0
    speed_mult: float = 1.0
    hp: float = 100.0
    max_hp: float = 100.0
    damage: float = 16.0
    fire_rate: float = 0.55      # secondes entre deux tirs
    shot_timer: float = 0.0
    arrows: int = 1
    pierce: int = 0
    crit: float = 0.05
    back_arrow: bool = False
    lifesteal: int = 0
    invuln: float = 0.0
    hit_flash: float = 0.0
    facing: float = -math.pi / 2
    moving: bool = False


@dataclass(eq=False)  # eq=False -> hashable par identité (utilisé dans Projectile.hits)
class Enemy:
    kind: str
    x: float
    y: float
    r: float
    hp: float
    max_hp: float
    speed: float
    dmg: float
    color: tuple
    dark: tuple
    shoot_cd: float = 0.0
    touch_cd: float = 0.0
    spawn_t: float = 0.0
    hit_flash: float = 0.0
    state: str = "idle"          # dasher : idle -> windup -> dash
    timer: float = 0.0
    dir_x: float = 0.0
    dir_y: float = 0.0
    phase: int = 1               # boss : 2 sous 50 % PV
    burst_cd: float = 0.0

    @property
    def boss(self) -> bool:
        return self.kind == "boss"

    @property
    def active(self) -> bool:
        return self.spawn_t <= 0 and self.hp > 0


ENEMY_STATS = {
    "chaser": dict(r=15, hp=28, speed=(80, 105), dmg=9, color=(255, 91, 91), dark=(165, 34, 34)),
    "shooter": dict(r=14, hp=20, speed=(70, 70), dmg=8, color=(192, 123, 255), dark=(106, 47, 160)),
    "tank": dict(r=21, hp=75, speed=(52, 52), dmg=15, color=(255, 154, 60), dark=(138, 76, 20)),
    "dasher": dict(r=13, hp=22, speed=(55, 65), dmg=11, color=(80, 220, 200), dark=(20, 110, 100)),
    "boss": dict(r=34, hp=280, speed=(62, 62), dmg=20, color=(255, 46, 46), dark=(107, 0, 0)),
}


def make_enemy(kind: str, x: float, y: float, room: int, rng) -> Enemy:
    s = ENEMY_STATS[kind]
    hp = s["hp"] * (1 + (room - 1) * 0.14)
    dmg = s["dmg"] * (1 + (room - 1) * 0.04)
    e = Enemy(kind=kind, x=x, y=y, r=s["r"], hp=hp, max_hp=hp,
              speed=rng.uniform(*s["speed"]), dmg=dmg,
              color=s["color"], dark=s["dark"], spawn_t=SPAWN_TIME)
    if kind == "shooter":
        e.shoot_cd = rng.uniform(0.8, 1.6)
    elif kind == "dasher":
        e.timer = rng.uniform(1.0, 2.0)
    elif kind == "boss":
        e.shoot_cd = 1.2
        e.burst_cd = 2.6
    return e


@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    r: float
    dmg: float = 0.0
    pierce_left: int = 0
    hits: set = field(default_factory=set)


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: tuple
    r: float


@dataclass
class Floater:
    x: float
    y: float
    text: str
    color: tuple
    life: float = 0.8
    vy: float = -46.0
    big: bool = False


@dataclass
class Coin:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    val: int = 1
