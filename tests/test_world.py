"""Tests de la logique pure (aucun besoin de pygame ni d'écran)."""
import math
import random

import pytest

from archer.config import DOOR_X, DOOR_W, ARENA_Y
from archer.entities import make_enemy
from archer.upgrades import BY_ID, roll_upgrades, reroll_cost
from archer.world import World

DT = 1 / 60


def run(world, seconds, move=(0.0, 0.0, 0.0)):
    for _ in range(int(seconds / DT)):
        world.update(DT, move)


def test_room_one_has_three_enemies_far_from_player():
    for seed in range(40):
        w = World(seed)
        assert len(w.enemies) == 3
        p = w.player
        assert all(math.hypot(e.x - p.x, e.y - p.y) >= 180 for e in w.enemies)


def test_every_fifth_room_is_a_single_boss():
    w = World(1)
    w.room = 4
    w.next_room()
    assert w.is_boss_room
    assert [e.kind for e in w.enemies] == ["boss"]


def test_enemies_are_harmless_while_spawning():
    w = World(2)
    e = w.enemies[0]
    e.x, e.y = w.player.x, w.player.y
    w.update(DT)
    assert w.player.hp == w.player.max_hp


def test_player_shoots_only_when_standing_still():
    w = World(3)
    run(w, 1.0, move=(1.0, 0.0, 1.0))
    assert "shoot" not in w.events
    w.events.clear()
    run(w, 1.5)
    assert "shoot" in w.events


def test_clearing_room_opens_door_and_exit_works():
    w = World(4)
    w.enemies.clear()
    w.update(DT)
    assert w.door_open and "door" in w.events
    w.player.x = DOOR_X + DOOR_W / 2
    run(w, 3.0, move=(0.0, -1.0, 1.0))
    assert w.exited
    assert w.player.y >= ARENA_Y


def test_player_dies():
    w = World(5)
    w.player.hp = 1
    w._hurt_player(10, 0.5)
    w.update(DT)
    assert w.dead and w.player.hp == 0


def test_rolled_upgrades_are_unique_and_available():
    w = World(6)
    w.player.arrows = 5
    w.player.back_arrow = True
    for seed in range(200):
        picks = roll_upgrades(w, random.Random(seed))
        ids = [u.id for u in picks]
        assert len(picks) == 3 and len(set(ids)) == 3
        assert "multishot" not in ids and "back" not in ids
        assert "heal" not in ids  # PV au max


def test_apply_upgrade_counts_and_effect():
    w = World(7)
    base = w.player.damage
    w.apply_upgrade(BY_ID["dmg"])
    assert w.player.damage == pytest.approx(base * 1.18)
    assert w.upgrade_counts["dmg"] == 1


def test_lifesteal_heals_on_kill():
    w = World(8)
    w.player.lifesteal = 3
    w.player.hp = 50
    e = w.enemies[0]
    w._damage_enemy(e, e.hp + 1, False)
    assert w.player.hp == 53 and w.kills == 1 and w.coins


def test_boss_enrages_below_half_hp():
    rng = random.Random(0)
    w = World(9)
    boss = make_enemy("boss", 480, 150, 5, rng)
    boss.spawn_t = 0
    w.enemies = [boss]
    boss.hp = boss.max_hp * 0.4
    w.update(DT)
    assert boss.phase == 2 and "boss_phase" in w.events


def test_reroll_cost_increases():
    assert reroll_cost(0) < reroll_cost(1) < reroll_cost(2)


def test_long_random_simulation_is_stable():
    rng = random.Random(42)
    for seed in range(5):
        w = World(seed)
        for i in range(60 * 90):
            if w.dead:
                w.reset()
            if w.exited:
                w.apply_upgrade(w.roll_choices()[0])
                w.next_room()
            a = rng.uniform(0, math.tau)
            move = (math.cos(a), math.sin(a), 1.0) if i % 90 < 30 else (0, 0, 0)
            w.update(DT, move)
            p = w.player
            assert 0 <= p.hp <= p.max_hp
