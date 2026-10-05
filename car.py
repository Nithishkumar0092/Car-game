"""
car.py
Car classes:
  Base     — shared geometry & drawing helpers
  PlayerCar — moves LEFT / RIGHT / UP / DOWN within road bounds
  EnemyCar  — moves downward, colour-coded by index
"""

import pygame
class Car:
    WIDTH  = 50
    HEIGHT = 85

    def __init__(self, x, y, color):
        self.x     = float(x)
        self.y     = float(y)
        self.color = color
        self.speed = 5
        self.rect  = pygame.Rect(int(x), int(y), self.WIDTH, self.HEIGHT)

    def update_rect(self):
        self.rect = pygame.Rect(int(self.x), int(self.y), self.WIDTH, self.HEIGHT)
    def _draw_wheels(self, screen):
        tyre = (20, 20, 20)
        hub  = (90, 90, 90)
        for ox, oy in [(-9, 10), (self.WIDTH - 1, 10),
                       (-9, 58), (self.WIDTH - 1, 58)]:
            pygame.draw.rect(screen, tyre,
                             (int(self.x)+ox, int(self.y)+oy, 10, 18),
                             border_radius=3)
            pygame.draw.rect(screen, hub,
                             (int(self.x)+ox+2, int(self.y)+oy+5, 6, 8),
                             border_radius=2)
class PlayerCar(Car):
    COLOR = (30, 120, 255)

    def __init__(self, x, y):
        super().__init__(x, y, self.COLOR)
        self.speed        = 6    
        self.vert_speed   = 4    
        self.turbo_active = False

    def move(self, keys, road_left, road_right,
             road_top=55, road_bottom=700):
        """
        Arrow keys:
          LEFT  / RIGHT — change lane
          UP            — move car forward (up screen) – faster dodge
          DOWN          — move car backward (down screen) – drop back
        """
        if keys[pygame.K_LEFT]  and self.x > road_left + 4:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x + self.WIDTH < road_right - 4:
            self.x += self.speed

        v = self.vert_speed
        if keys[pygame.K_UP]:
            if self.y > road_top:
                self.y -= v
            self.turbo_active = True
        else:
            self.turbo_active = False

        if keys[pygame.K_DOWN]:
            if self.y + self.HEIGHT < road_bottom:
                self.y += v

        self.update_rect()

    def draw(self, screen):
        bx, by = int(self.x), int(self.y)
        pygame.draw.rect(screen, self.color,
                         (bx, by, self.WIDTH, self.HEIGHT),
                         border_radius=10)
        pygame.draw.rect(screen, (70, 160, 255),
                         (bx+6, by+4, self.WIDTH-12, 14), border_radius=4)
        pygame.draw.rect(screen, (180, 230, 255),
                         (bx+8, by+10, self.WIDTH-16, 22), border_radius=5)
        pygame.draw.rect(screen, (180, 230, 255),
                         (bx+8, by+52, self.WIDTH-16, 16), border_radius=5)
        pygame.draw.ellipse(screen, (255, 255, 160),
                            (bx+4,  by+2, 14, 8))
        pygame.draw.ellipse(screen, (255, 255, 160),
                            (bx+self.WIDTH-18, by+2, 14, 8))
        pygame.draw.ellipse(screen, (255, 60, 60),
                            (bx+4,  by+self.HEIGHT-10, 12, 7))
        pygame.draw.ellipse(screen, (255, 60, 60),
                            (bx+self.WIDTH-16, by+self.HEIGHT-10, 12, 7))
        if self.turbo_active:
            flame = pygame.Surface((self.WIDTH, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(flame, (255, 150, 30, 160),
                                (5, 0, self.WIDTH-10, 20))
            screen.blit(flame, (bx, by + self.HEIGHT - 4))

        self._draw_wheels(screen)
class EnemyCar(Car):
    PALETTE = [
        (220, 50,  50),
        (50,  200, 80),   
        (240, 160, 20),   
        (180, 50,  220),  
        (230, 220, 40),   
        (50,  200, 200),  
        (210, 80,  140),  
        (255, 255, 255),  
        (80,  80,  220),
    ]

    def __init__(self, x, y, speed, index):
        color = self.PALETTE[index % len(self.PALETTE)]
        super().__init__(x, y, color)
        self.speed = speed

    def move(self):
        self.y += self.speed
        self.update_rect()

    def draw(self, screen):
        bx, by = int(self.x), int(self.y)
        lite = tuple(min(c+40, 255) for c in self.color)
        pygame.draw.rect(screen, self.color,
                         (bx, by, self.WIDTH, self.HEIGHT),
                         border_radius=10)
        pygame.draw.rect(screen, lite,
                         (bx+6, by+4, self.WIDTH-12, 14), border_radius=4)
        pygame.draw.rect(screen, (200, 240, 200),
                         (bx+8, by+10, self.WIDTH-16, 22), border_radius=5)
        pygame.draw.rect(screen, (200, 240, 200),
                         (bx+8, by+52, self.WIDTH-16, 16), border_radius=5)
        pygame.draw.ellipse(screen, (255, 80, 80),
                            (bx+4,  by+2, 14, 8))
        pygame.draw.ellipse(screen, (255, 80, 80),
                            (bx+self.WIDTH-18, by+2, 14, 8))
        pygame.draw.ellipse(screen, (255, 255, 160),
                            (bx+4,  by+self.HEIGHT-10, 12, 7))
        pygame.draw.ellipse(screen, (255, 255, 160),
                            (bx+self.WIDTH-16, by+self.HEIGHT-10, 12, 7))
        self._draw_wheels(screen)
