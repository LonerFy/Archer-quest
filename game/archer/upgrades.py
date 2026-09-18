"""Améliorations proposées entre les salles."""
from dataclasses import dataclass
from typing import Callable

RARE_WEIGHT = 0.45
MAX_FIRE_RATE = 0.18


@dataclass(frozen=True)
class Upgrade:
    id: str
    name: str
    desc: str
    rare: bool
    apply: Callable
    available: Callable = lambda w: True


def _count(w, uid):
    return w.upgrade_counts.get(uid, 0)


def _heal(w, amount):
    p = w.player
    p.hp = min(p.max_hp, p.hp + amount)


def _vitality(w):
    w.player.max_hp += 25
    _heal(w, 25)


UPGRADES = [
    Upgrade("dmg", "Force", "+18 % de dégâts", False,
            lambda w: setattr(w.player, "damage", w.player.damage * 1.18)),
    Upgrade("atkspd", "Cadence", "+16 % de vitesse de tir", False,
            lambda w: setattr(w.player, "fire_rate", max(MAX_FIRE_RATE, w.player.fire_rate * 0.84)),
            lambda w: w.player.fire_rate > MAX_FIRE_RATE + 1e-6),
    Upgrade("hp", "Vitalité", "+25 PV max et soigne 25 PV", False, _vitality),
    Upgrade("spd", "Agilité", "+10 % de vitesse de déplacement", False,
            lambda w: setattr(w.player, "speed_mult", w.player.speed_mult + 0.10),
            lambda w: _count(w, "spd") < 5),
    Upgrade("crit", "Précision", "+9 % de critique (dégâts x2)", False,
            lambda w: setattr(w.player, "crit", w.player.crit + 0.09),
            lambda w: w.player.crit < 0.6),
    Upgrade("heal", "Soin", "Restaure 50 % des PV max", False,
            lambda w: _heal(w, w.player.max_hp * 0.5),
            lambda w: w.player.hp < w.player.max_hp),
    Upgrade("gold", "Trésor", "+60 pièces d'or", False,
            lambda w: setattr(w, "gold", w.gold + 60)),
    Upgrade("multishot", "Multi-tir", "+1 flèche tirée en éventail", True,
            lambda w: setattr(w.player, "arrows", w.player.arrows + 1),
            lambda w: w.player.arrows < 5),
    Upgrade("pierce", "Perforation", "Les flèches transpercent 1 ennemi de plus", True,
            lambda w: setattr(w.player, "pierce", w.player.pierce + 1),
            lambda w: w.player.pierce < 3),
    Upgrade("back", "Tir arrière", "Une flèche part aussi dans votre dos", True,
            lambda w: setattr(w.player, "back_arrow", True),
            lambda w: not w.player.back_arrow),
    Upgrade("lifesteal", "Vampirisme", "+3 PV rendus par ennemi tué", True,
            lambda w: setattr(w.player, "lifesteal", w.player.lifesteal + 3),
            lambda w: w.player.lifesteal < 9),
]

BY_ID = {u.id: u for u in UPGRADES}


def roll_upgrades(world, rng, n: int = 3) -> list:
    """Tire n améliorations distinctes et disponibles (tirage pondéré sans remise)."""
    pool = [u for u in UPGRADES if u.available(world)]
    picks = []
    while pool and len(picks) < n:
        weights = [RARE_WEIGHT if u.rare else 1.0 for u in pool]
        choice = rng.choices(pool, weights)[0]
        picks.append(choice)
        pool.remove(choice)
    return picks


def reroll_cost(rerolls_done: int) -> int:
    return 20 + 15 * rerolls_done
