"""
effects.py
Visual crash effects:
  GlassShard   — spinning, fading polygon fragment
  ImpactFlash  — expanding orange ring burst
  ScreenShake  — camera shake offset
  CrashEffects — top-level manager
"""

import pygame
import random
import math


def _rotate(pts, cx, cy, deg):
    r = math.radians(deg)
    ca, sa = math.cos(r), math.sin(r)
    return [(cx+(px-cx)*ca-(py-cy)*sa,
             cy+(px-cx)*sa+(py-cy)*ca) for px, py in pts]
class GlassShard:
    COLOURS = [(200,235,255),(180,220,255),(220,245,255),
               (160,210,240),(255,255,255),(190,230,250)]

    def __init__(self, cx, cy):
        nv   = random.randint(3, 5)
        size = random.uniform(6, 24)
        self._local = []
        for i in range(nv):
            ang = 360/nv*i + random.uniform(-28, 28)
            r   = size * random.uniform(0.45, 1.0)
            self._local.append((math.cos(math.radians(ang))*r,
                                 math.sin(math.radians(ang))*r))
        self.x  = float(cx) + random.uniform(-22, 22)
        self.y  = float(cy) + random.uniform(-22, 22)
        ang     = random.uniform(0, 360)
        sp      = random.uniform(3, 13)
        self.vx = math.cos(math.radians(ang)) * sp
        self.vy = math.sin(math.radians(ang)) * sp - random.uniform(1, 5)
        self.rot_speed = random.uniform(-16, 16)
        self.angle     = random.uniform(0, 360)
        self.gravity   = random.uniform(0.28, 0.58)
        self.alpha     = 255
        self.fade      = random.uniform(3, 8)
        self.colour    = random.choice(self.COLOURS)
        self.alive     = True

    def update(self):
        self.x    += self.vx;  self.y += self.vy
        self.vy   += self.gravity;  self.vx *= 0.985
        self.angle += self.rot_speed
        self.alpha  = max(0, self.alpha - self.fade)
        if self.alpha == 0: self.alive = False

    def draw(self, surface):
        if not self.alive: return
        wp = _rotate([(self.x+lx, self.y+ly) for lx, ly in self._local],
                     self.x, self.y, self.angle)
        ip = [(int(p[0]), int(p[1])) for p in wp]
        if len(ip) < 3: return
        xs, ys = [p[0] for p in ip], [p[1] for p in ip]
        w = max(max(xs)-min(xs)+1, 1);  h = max(max(ys)-min(ys)+1, 1)
        ox, oy = min(xs), min(ys)
        try:
            tmp = pygame.Surface((w, h), pygame.SRCALPHA)
            lp  = [(p[0]-ox, p[1]-oy) for p in ip]
            pygame.draw.polygon(tmp, (*self.colour, int(self.alpha)), lp)
            pygame.draw.polygon(tmp, (255,255,255, min(255,int(self.alpha*1.2))), lp, 1)
            surface.blit(tmp, (ox, oy))
        except Exception:
            pass
class ImpactFlash:
    def __init__(self, cx, cy):
        self.cx = cx;  self.cy = cy
        self.radius = 8;  self.alpha = 255;  self.alive = True

    def update(self):
        self.radius += 9
        self.alpha   = max(0, self.alpha - 16)
        if self.alpha == 0: self.alive = False

    def draw(self, surface):
        if not self.alive or self.radius < 1: return
        r = int(self.radius)
        try:
            ring = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 160, 30, int(self.alpha)),
                               (r+2, r+2), r, 4)
            surface.blit(ring, (self.cx-r-2, self.cy-r-2))
        except Exception:
            pass
        if self.radius < 55:
            gr = max(1, int(self.radius*0.5))
            try:
                gw = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
                pygame.draw.circle(gw, (255,255,210, min(255,int(self.alpha+50))),
                                   (gr, gr), gr)
                surface.blit(gw, (self.cx-gr, self.cy-gr))
            except Exception:
                pass
class ScreenShake:
    def __init__(self):
        self.intensity = 0;  self.duration = 0

    def trigger(self, intensity=12, duration=32):
        self.intensity = intensity;  self.duration = duration

    def update(self):
        if self.duration > 0:
            self.duration  -= 1
            self.intensity *= 0.87

    def offset(self):
        if self.duration > 0 and self.intensity > 0.5:
            return (int(random.uniform(-self.intensity, self.intensity)),
                    int(random.uniform(-self.intensity, self.intensity)))
        return 0, 0
class GlassEffect:
    N = 60

    def __init__(self):
        self.shards  = [];  self.flashes = [];  self.active = False

    def spawn(self, cx, cy):
        self.shards  = [GlassShard(cx, cy) for _ in range(self.N)]
        self.flashes = [ImpactFlash(cx, cy),
                        ImpactFlash(cx+random.randint(-28,28),
                                    cy+random.randint(-28,28))]
        self.active  = True

    def update(self):
        self.shards  = [s for s in self.shards  if s.alive]
        self.flashes = [f for f in self.flashes if f.alive]
        for s in self.shards:  s.update()
        for f in self.flashes: f.update()
        if not self.shards and not self.flashes: self.active = False

    def draw(self, surface):
        for f in self.flashes: f.draw(surface)
        for s in self.shards:  s.draw(surface)


class CrashEffects:
    def __init__(self, sw, sh):
        self.sw = sw;  self.sh = sh
        self.glass = GlassEffect();  self.shake = ScreenShake()
        self._done = False

    def trigger(self, rect):
        if self._done: return
        self.glass.spawn(rect.centerx, rect.centery)
        self.shake.trigger(intensity=14, duration=35)
        self._done = True

    def reset(self):
        self.glass = GlassEffect();  self.shake = ScreenShake()
        self._done = False

    def update(self):
        self.glass.update();  self.shake.update()

    def draw(self, surface):
        self.glass.draw(surface)

    def get_shake_offset(self):
        return self.shake.offset()

    @property
    def active(self):
        return self.glass.active or self.shake.duration > 0
