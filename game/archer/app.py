"""Boucle principale, états et entrées."""
import asyncio
import math
import sys

import pygame

from . import layout as L
from .audio import Audio
from .config import W, H, FPS, MAX_DT
from .render import Renderer
from .storage import load_save, write_save
from .upgrades import reroll_cost
from .world import World

WEB = sys.platform == "emscripten"

KEYS_LEFT = (pygame.K_LEFT, pygame.K_a, pygame.K_q)
KEYS_RIGHT = (pygame.K_RIGHT, pygame.K_d)
KEYS_UP = (pygame.K_UP, pygame.K_w, pygame.K_z)
KEYS_DOWN = (pygame.K_DOWN, pygame.K_s)
KEYS_CONFIRM = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
KEYS_PAUSE = (pygame.K_ESCAPE, pygame.K_p)


class PointerStick:
    """Joystick virtuel : maintenir puis glisser (souris ou doigt)."""
    DEAD, MAXR = 8, 55

    def __init__(self):
        self.pointer = False
        self.start = self.cur = (0, 0)

    def vector(self):
        keys = pygame.key.get_pressed()
        kx = any(keys[k] for k in KEYS_RIGHT) - any(keys[k] for k in KEYS_LEFT)
        ky = any(keys[k] for k in KEYS_DOWN) - any(keys[k] for k in KEYS_UP)
        if kx or ky:
            n = math.hypot(kx, ky)
            return kx / n, ky / n, 1.0
        if not self.pointer:
            return 0.0, 0.0, 0.0
        dx, dy = self.cur[0] - self.start[0], self.cur[1] - self.start[1]
        d = math.hypot(dx, dy)
        if d < self.DEAD:
            return 0.0, 0.0, 0.0
        mag = (min(d, self.MAXR) - self.DEAD) / (self.MAXR - self.DEAD)
        return dx / d, dy / d, min(1.0, mag)


class App:
    def __init__(self):
        if not WEB:
            pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        flags = 0 if WEB else pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((W, H), flags)
        pygame.display.set_caption("Archer Quest")
        self.splash("Chargement...")  # une image tout de suite, avant tout calcul
        self.clock = pygame.time.Clock()
        self.world = World()
        self.renderer = Renderer()
        self.audio = Audio()
        self.stick = PointerStick()
        self.save = load_save()
        self.best_room = int(self.save.get("best_room", 0))
        self.audio.muted = bool(self.save.get("muted", False))
        self.state = "title"
        self.fade = 0.0
        self.choices = []
        self.rerolls = 0
        self.best_at_start = self.best_room
        self.running = True
        self.t = 0.0

    def splash(self, message):
        """Affiche un message immédiatement (démarrage, erreur)."""
        self.screen.fill((8, 8, 14))
        font = pygame.font.Font(None, 40)
        img = font.render(message, True, (255, 215, 94))
        self.screen.blit(img, img.get_rect(center=(W // 2, H // 2)))
        pygame.display.flip()

    # ------------------------------------------------------------------ boucle
    async def run(self):
        while self.running:
            dt = min(MAX_DT, self.clock.tick(FPS) / 1000)
            if not self.audio.ready:
                self.audio.build_step()
            self.step(dt, pygame.event.get())
            pygame.display.flip()
            await asyncio.sleep(0)  # indispensable pour pygbag (navigateur)
        if not WEB:
            pygame.quit()

    def step(self, dt, events):
        self.t += dt
        for ev in events:
            self.handle(ev)
        self.update(dt)
        self.draw()

    # ------------------------------------------------------------------ transitions
    def persist(self):
        self.save.update(best_room=self.best_room, muted=self.audio.muted)
        write_save(self.save)

    def start_game(self):
        self.world.reset()
        self.stick.pointer = False
        self.best_at_start = self.best_room
        self.state = "playing"
        self.audio.play("select")

    def toggle_mute(self):
        self.audio.muted = not self.audio.muted
        self.persist()

    def pause(self):
        if self.state == "playing":
            self.state = "paused"
            self.stick.pointer = False

    def open_upgrades(self):
        self.choices = self.world.roll_choices()
        self.rerolls = 0
        self.state = "upgrade"
        self.audio.play("levelup")

    def choose(self, index):
        if index >= len(self.choices):
            return
        self.world.apply_upgrade(self.choices[index])
        self.world.next_room()
        if self.world.room > self.best_room:
            self.best_room = self.world.room
            self.persist()
        self.audio.play("select")
        self.state = "playing"

    def reroll(self):
        cost = reroll_cost(self.rerolls)
        if self.world.gold < cost:
            self.audio.play("deny")
            return
        self.world.gold -= cost
        self.rerolls += 1
        self.choices = self.world.roll_choices()
        self.audio.play("gold")

    def game_over(self):
        self.state = "gameover"
        self.stick.pointer = False
        if self.world.room > self.best_room:
            self.best_room = self.world.room
        self.persist()

    # ------------------------------------------------------------------ entrées
    def handle(self, ev):
        if ev.type == pygame.QUIT and not WEB:
            self.running = False
        elif ev.type == pygame.WINDOWFOCUSLOST:
            self.pause()
        elif ev.type == pygame.KEYDOWN:
            self.on_key(ev.key)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.on_click(ev.pos)
        elif ev.type == pygame.MOUSEMOTION and self.stick.pointer:
            self.stick.cur = ev.pos
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.stick.pointer = False

    def on_key(self, key):
        if key == pygame.K_m:
            self.toggle_mute()
        elif self.state in ("title", "gameover") and key in KEYS_CONFIRM:
            self.start_game()
        elif self.state == "playing" and key in KEYS_PAUSE:
            self.pause()
        elif self.state == "paused" and (key in KEYS_PAUSE or key in KEYS_CONFIRM):
            self.state = "playing"
        elif self.state == "upgrade":
            digits = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
                      pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2,
                      pygame.K_AMPERSAND: 0, ord("é"): 1, pygame.K_QUOTEDBL: 2}  # rangée AZERTY
            if key in digits:
                self.choose(digits[key])
            elif key == pygame.K_r:
                self.reroll()

    def on_click(self, pos):
        if self.state == "title":
            self.start_game()
        elif self.state == "playing":
            if L.PAUSE_BTN.collidepoint(pos):
                self.pause()
            elif L.SOUND_BTN.collidepoint(pos):
                self.toggle_mute()
            else:
                self.stick.pointer = True
                self.stick.start = self.stick.cur = pos
        elif self.state == "paused":
            if L.RESUME_BTN.collidepoint(pos):
                self.state = "playing"
            elif L.MENU_BTN.collidepoint(pos):
                self.world.reset()
                self.state = "title"
            elif L.SOUND_BTN.collidepoint(pos):
                self.toggle_mute()
        elif self.state == "upgrade":
            for i, rect in enumerate(L.card_rects(len(self.choices))):
                if rect.collidepoint(pos):
                    self.choose(i)
                    return
            if L.REROLL_BTN.collidepoint(pos):
                self.reroll()
        elif self.state == "gameover" and L.RETRY_BTN.collidepoint(pos):
            self.start_game()

    # ------------------------------------------------------------------ update / draw
    def update(self, dt):
        if self.state == "playing":
            self.world.update(dt, self.stick.vector())
            for name in dict.fromkeys(self.world.events):  # un son par type par frame
                self.audio.play(name)
            self.world.events.clear()
            if self.world.dead:
                self.game_over()
            elif self.world.exited:
                self.state = "transition"
                self.fade = 0.0
                self.stick.pointer = False
        elif self.state == "transition":
            self.fade += dt * 2.2
            if self.fade >= 1:
                self.open_upgrades()

    def draw(self):
        r, s, w = self.renderer, self.screen, self.world
        mouse = pygame.mouse.get_pos()
        r.draw_world(s, w, self.t, self.stick if self.state == "playing" else None)
        if self.state in ("playing", "paused", "transition"):
            r.draw_hud(s, w, self.audio.muted, self.best_room)
        if self.state == "transition":
            r.draw_fade(s, self.fade)
        elif self.state == "paused":
            r.draw_pause(s, mouse)
        elif self.state == "upgrade":
            r.draw_upgrade(s, w, self.choices, reroll_cost(self.rerolls), mouse)
        elif self.state == "title":
            r.draw_title(s, self.best_room, mouse)
        elif self.state == "gameover":
            r.draw_gameover(s, w, self.best_room, self.best_room > self.best_at_start, mouse)
