"""
game.py — Highway Rush
All gameplay features:
  • 4-direction player movement (←→ lanes, ↑↓ forward/backward)
  • Continuous smooth acceleration (real-car feel)
  • Level system with increasing difficulty labels
  • BGM + engine pitch-shift + crash sound + glass sound
  • Visual glass shards + impact flash + screen shake on crash
  • Speedometer bar + gear-up flash
  • Persistent high score
"""

import pygame
import random
import os
from car import PlayerCar, EnemyCar
from sounds import SoundManager
from effects import CrashEffects
SCREEN_W  = 620
SCREEN_H  = 720
FPS       = 60

ROAD_L    = 130
ROAD_R    = 490
ROAD_W    = ROAD_R - ROAD_L
LANES     = 3
LANE_W    = ROAD_W // LANES

ROAD_TOP    = 55    
ROAD_BOTTOM = SCREEN_H - 10
START_SPEED   = 3.0   
MAX_SPEED     = 32.0  
ACCEL_RATE    = 0.004 
PLAYER_LAT    = 7     
PLAYER_VERT   = 5    


LEVELS = [
    {"threshold": 0,    "name": "Learner",    "colour": (100,220,100)},
    {"threshold": 7,    "name": "Driver",     "colour": (180,220,60)},
    {"threshold": 12,   "name": "Racer",      "colour": (220,180,40)},
    {"threshold": 17,   "name": "Pro",        "colour": (255,140,20)},
    {"threshold": 22,   "name": "Extreme",    "colour": (255,80,30)},
    {"threshold": 27,   "name": "INSANE",     "colour": (255,40,40)},
]


BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
YELLOW     = (255, 220, 0)
RED        = (210, 40,  40)
ORANGE     = (255, 140, 0)
DARK_ROAD  = (42,  42,  42)
GRASS      = (32,  105, 32)
GRASS_LITE = (48,  135, 48)
HUD_BG     = (10,  10,  20)

HIGHSCORE_FILE = "highscore.txt"



def load_hs():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            return int(open(HIGHSCORE_FILE).read().strip())
        except Exception:
            return 0
    return 0

def save_hs(score):
    if score > load_hs():
        open(HIGHSCORE_FILE, "w").write(str(score))


class Road:
    STRIPE_H   = 55
    STRIPE_GAP = 38
    STRIPE_W   = 7

    def __init__(self):
        self.offset = 0.0

    def update(self, speed):
        self.offset = (self.offset + speed) % (self.STRIPE_H + self.STRIPE_GAP)

    def draw(self, s):
        pygame.draw.rect(s, GRASS,      (0,      0, ROAD_L,            SCREEN_H))
        pygame.draw.rect(s, GRASS,      (ROAD_R, 0, SCREEN_W - ROAD_R, SCREEN_H))
        pygame.draw.rect(s, GRASS_LITE, (ROAD_L-15, 0, 15, SCREEN_H))
        pygame.draw.rect(s, GRASS_LITE, (ROAD_R,    0, 15, SCREEN_H))
        pygame.draw.rect(s, DARK_ROAD, (ROAD_L, 0, ROAD_W, SCREEN_H))
        pygame.draw.rect(s, WHITE, (ROAD_L,     0, 5, SCREEN_H))
        pygame.draw.rect(s, WHITE, (ROAD_R - 5, 0, 5, SCREEN_H))
        for lane in range(1, LANES):
            x = ROAD_L + lane * LANE_W - self.STRIPE_W // 2
            y = int(-self.STRIPE_H + self.offset)
            while y < SCREEN_H:
                pygame.draw.rect(s, YELLOW,
                                 (x, y, self.STRIPE_W, self.STRIPE_H))
                y += self.STRIPE_H + self.STRIPE_GAP

class Speedometer:
    X, Y, W, H = 6, 58, 118, 14

    def draw(self, s, speed, max_speed, font):
        ratio = min(speed / max_speed, 1.0)
        pygame.draw.rect(s, (25,25,25), (self.X, self.Y, self.W, self.H),
                         border_radius=5)
        fw = int(self.W * ratio)
        if fw > 0:
            c = ((50,220,80)  if ratio < 0.35 else
                 (200,200,30) if ratio < 0.60 else
                 (255,140,20) if ratio < 0.82 else
                 (255,40,40))
            pygame.draw.rect(s, c,
                             (self.X, self.Y, fw, self.H), border_radius=5)
        pygame.draw.rect(s, (140,140,140),
                         (self.X, self.Y, self.W, self.H), 2, border_radius=5)
        lbl = font.render(f"SPD {speed:4.1f}", True, WHITE)
        s.blit(lbl, (self.X, self.Y + self.H + 3))


class LevelBadge:
    def draw(self, s, level_info, font_md, font_sm, flash_alpha):
        name   = level_info["name"]
        colour = level_info["colour"]
        badge  = font_md.render(name, True, colour)
        s.blit(badge, (ROAD_L + ROAD_W//2 - badge.get_width()//2, 8))
        if flash_alpha > 0:
            fl = pygame.Surface((ROAD_W, SCREEN_H), pygame.SRCALPHA)
            fl.fill((*colour, flash_alpha))
            s.blit(fl, (ROAD_L, 0))
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.world  = pygame.Surface((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Highway Rush")
        self.clock  = pygame.time.Clock()

        self.f_xl  = pygame.font.SysFont("Arial", 54, bold=True)
        self.f_lg  = pygame.font.SysFont("Arial", 36, bold=True)
        self.f_md  = pygame.font.SysFont("Arial", 26, bold=True)
        self.f_sm  = pygame.font.SysFont("Arial", 19)
        self.f_xs  = pygame.font.SysFont("Arial", 14)

        self.sounds  = SoundManager()
        self.sounds.build()
        self.effects = CrashEffects(SCREEN_W, SCREEN_H)
        self.speedo  = Speedometer()
        self.badge   = LevelBadge()

        self.highscore = load_hs()
        self.state     = "menu"
        self._reset()
    def _reset(self):
        sx = ROAD_L + LANE_W + (LANE_W - PlayerCar.WIDTH) // 2
        self.player       = PlayerCar(sx, SCREEN_H - 150)
        self.player.speed = PLAYER_LAT
        self.player.vert_speed = PLAYER_VERT

        self.road         = Road()
        self.enemies      = []
        self.score        = 0

        self.road_speed   = START_SPEED
        self.enemy_speed  = START_SPEED
        self.frame_count  = 0

        self.spawn_timer    = 0
        self.spawn_interval = 100
        self.enemy_count    = 0

        self._cur_level     = 0     
        self._level_flash   = 0    
        self._gear_flash    = 0     

        self.effects.reset()

    def _get_level_info(self):
        info = LEVELS[0]
        for lvl in LEVELS:
            if self.road_speed >= lvl["threshold"]:
                info = lvl
        return info

    def _check_level_up(self):
        new_idx = 0
        for i, lvl in enumerate(LEVELS):
            if self.road_speed >= lvl["threshold"]:
                new_idx = i
        if new_idx > self._cur_level:
            self._cur_level  = new_idx
            self._level_flash = 200  

    def _accelerate(self):
        self.frame_count += 1
        ease = FPS * 4
        t    = min(self.frame_count / ease, 1.0)
        accel = ACCEL_RATE * (0.25 + 0.75 * t)  

        prev = self.road_speed
        self.road_speed  = min(self.road_speed + accel, MAX_SPEED)
        self.enemy_speed = self.road_speed
        if int(self.road_speed) > int(prev):
            self._gear_flash = 160

        self.player.speed      = PLAYER_LAT + (self.road_speed - START_SPEED) * 0.15
        self.player.vert_speed = PLAYER_VERT + (self.road_speed - START_SPEED) * 0.12

        ratio = (self.road_speed - START_SPEED) / (MAX_SPEED - START_SPEED)
        self.spawn_interval = max(28, int(105 - ratio * 77))

        self._check_level_up()

    def _spawn_enemy(self):
        lane  = random.randint(0, LANES - 1)
        x     = ROAD_L + lane * LANE_W + (LANE_W - EnemyCar.WIDTH) // 2
        enemy = EnemyCar(x, -EnemyCar.HEIGHT - 10,
                         self.enemy_speed, self.enemy_count)
        for e in self.enemies:
            if abs(e.x - x) < EnemyCar.WIDTH and e.y < 100:
                return
        self.enemies.append(enemy)
        self.enemy_count += 1
    def _collides(self):
        pr = self.player.rect.inflate(-8, -8)
        for e in self.enemies:
            if pr.colliderect(e.rect.inflate(-8, -8)):
                return True
        return False
    def _draw_hud(self, s):
        # Top strip
        pygame.draw.rect(s, HUD_BG, (ROAD_L, 0, ROAD_W, 52))
        pygame.draw.rect(s, HUD_BG, (0, 0, ROAD_L, 95)) 

        # Score
        s.blit(self.f_md.render(f"Score: {self.score}", True, WHITE),
               (ROAD_L + 8, 14))
        hs_txt = self.f_sm.render(f"Best:{self.highscore}", True, (190,190,190))
        s.blit(hs_txt, (ROAD_R + 4, 10))
        mute_c = (200,80,80) if self.sounds.muted else (100,100,100)
        s.blit(self.f_xs.render("M=mute", True, mute_c), (ROAD_R + 4, 34))
        self.speedo.draw(s, self.road_speed, MAX_SPEED, self.f_xs)
        lvl_info = self._get_level_info()
        self.badge.draw(s, lvl_info, self.f_md, self.f_xs, self._level_flash)
        if self._level_flash > 0:
            self._level_flash = max(0, self._level_flash - 14)
        if self._gear_flash > 0:
            fl = pygame.Surface((ROAD_W, SCREEN_H), pygame.SRCALPHA)
            fl.fill((80, 255, 120, self._gear_flash))
            s.blit(fl, (ROAD_L, 0))
            self._gear_flash = max(0, self._gear_flash - 18)
        for i, txt in enumerate(["↑↓ Fwd/Back", "←→ Lanes"]):
            s.blit(self.f_xs.render(txt, True, (90,90,90)), (4, SCREEN_H - 30 + i*14))
    def _cx(self, surf, y):
        return (SCREEN_W//2 - surf.get_width()//2, y)
    def _draw_menu(self, s):
        s.fill((12, 12, 30))
        pygame.draw.rect(s, DARK_ROAD, (ROAD_L, 0, ROAD_W, SCREEN_H))
        pygame.draw.rect(s, WHITE, (ROAD_L,     0, 5, SCREEN_H))
        pygame.draw.rect(s, WHITE, (ROAD_R - 5, 0, 5, SCREEN_H))
        ov = pygame.Surface((ROAD_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 25, 205))
        s.blit(ov, (ROAD_L, 0))

        t = self.f_xl.render("HIGHWAY RUSH", True, YELLOW)
        s.blit(t, self._cx(t, 90))

        sub = self.f_sm.render("Survive the highway — speed never stops rising!", True, WHITE)
        s.blit(sub, self._cx(sub, 168))

        controls = [
            ("← →",  "Change lane"),
            ("↑",    "Move forward / dodge"),
            ("↓",    "Move backward / drop back"),
            ("M",    "Toggle sound on/off"),
            ("ESC",  "Quit"),
        ]
        for i, (key, desc) in enumerate(controls):
            kw = self.f_sm.render(key,  True, YELLOW)
            dw = self.f_sm.render(desc, True, (180,180,180))
            base_x = SCREEN_W//2 - 90
            base_y = 220 + i * 32
            s.blit(kw, (base_x, base_y))
            s.blit(dw, (base_x + 60, base_y))
        s.blit(self.f_xs.render("LEVELS:", True, (130,130,130)),
               self._cx(self.f_xs.render("LEVELS:", True, WHITE), 385))
        for i, lvl in enumerate(LEVELS):
            lw = self.f_xs.render(f"  {lvl['name']:10}  speed ≥ {lvl['threshold']}",
                                  True, lvl["colour"])
            s.blit(lw, self._cx(lw, 400 + i*17))

        hs = self.f_md.render(f"Best Score: {self.highscore}", True, (255,200,50))
        s.blit(hs, self._cx(hs, 508))

        if pygame.time.get_ticks() % 1100 < 660:
            go = self.f_lg.render("Press ENTER to Start", True, (80,255,120))
            s.blit(go, self._cx(go, 550))

        eq = self.f_sm.render("ESC — Quit", True, (100,100,100))
        s.blit(eq, self._cx(eq, 605))
    def _draw_gameover(self, s):
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 178))
        s.blit(ov, (0, 0))

        go = self.f_xl.render("GAME OVER", True, RED)
        s.blit(go, self._cx(go, 175))

        sc = self.f_lg.render(f"Score: {self.score}", True, WHITE)
        s.blit(sc, self._cx(sc, 260))

        sp = self.f_md.render(
            f"Top Speed: {self.road_speed:.1f}  |  Level: {self._get_level_info()['name']}",
            True, ORANGE)
        s.blit(sp, self._cx(sp, 315))

        hs = self.f_md.render(f"Best: {self.highscore}", True, YELLOW)
        s.blit(hs, self._cx(hs, 362))

        if self.score > 0 and self.score >= self.highscore:
            nb = self.f_md.render("✦ New High Score! ✦", True, (255, 215, 0))
            s.blit(nb, self._cx(nb, 408))

        if pygame.time.get_ticks() % 1100 < 660:
            rt = self.f_lg.render("ENTER — Restart", True, (80,255,120))
            s.blit(rt, self._cx(rt, 468))

        eq = self.f_sm.render("ESC — Quit", True, (150,150,150))
        s.blit(eq, self._cx(eq, 535))

    def _scene_playing(self):
        self._accelerate()
        keys = pygame.key.get_pressed()
        self.player.move(keys, ROAD_L, ROAD_R, ROAD_TOP, ROAD_BOTTOM)
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self._spawn_enemy()
            self.spawn_timer = 0
        for e in self.enemies:
            e.speed = self.enemy_speed
            e.move()
        before = len(self.enemies)
        self.enemies = [e for e in self.enemies if e.y < SCREEN_H + 130]
        self.score  += (before - len(self.enemies)) * 10

        self.road.update(self.road_speed)
        self.sounds.update_engine_pitch(self.road_speed, MAX_SPEED)
        if self._collides():
            save_hs(self.score)
            self.highscore = load_hs()
            self.sounds.stop_engine()
            self.sounds.stop_bgm()
            self.sounds.play_crash()
            self.sounds.play_glass()
            self.effects.trigger(self.player.rect)
            self.state = "gameover"
        self.road.draw(self.world)
        for e in self.enemies:
            e.draw(self.world)
        self.player.draw(self.world)
        self._draw_hud(self.world)
    def _scene_gameover(self):
        self.effects.update()
        self.road.draw(self.world)
        for e in self.enemies:
            e.draw(self.world)
        self.player.draw(self.world)
        self.effects.draw(self.world)     
        self._draw_hud(self.world)
        self._draw_gameover(self.world)
    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    if event.key == pygame.K_RETURN:
                        if self.state in ("menu", "gameover"):
                            self._reset()
                            self.state = "playing"
                            self.sounds.start_engine()
                            self.sounds.start_bgm()

                    if event.key == pygame.K_m:
                        muted = self.sounds.toggle_mute()
                        print("Sound:", "OFF" if muted else "ON")
                if event.type == pygame.USEREVENT + 1:
                    self.sounds.trigger_glass_now()
            self.world.fill(BLACK)

            if self.state == "menu":
                self._draw_menu(self.world)
            elif self.state == "playing":
                self._scene_playing()
            elif self.state == "gameover":
                self._scene_gameover()
            ox, oy = self.effects.get_shake_offset()
            self.screen.fill(BLACK)
            self.screen.blit(self.world, (ox, oy))
            pygame.display.flip()

        pygame.quit()
