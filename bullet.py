import math, pygame #Importing modules math + pygame.
from constants import W, BULLET_SPEED #Importing in from constants.py we're grabbing the width and bullet speed.


class Bullet:
    def __init__(self, x, y, angle=0.0, dmg=1, pierc=1): #Inside the brackets it sets the default values for the bullet as the game progresses there are upgrades.
        self.x, self.y = float(x), float(y)
        self.dmg, self.pierc, self.alive = dmg, pierc, True
        r = math.radians(angle)
        self.vx = math.sin(r) * BULLET_SPEED
        self.vy = -math.cos(r) * BULLET_SPEED
        self.rect = pygame.Rect(int(x) - 3, int(y) - 6, 6, 12)
        self.hit_segs = set()

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rect.center = (int(self.x), int(self.y))
        if self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > W:
            self.alive = False

    def draw(self, s):
        pygame.draw.rect(s, (100, 255, 255), self.rect)#Drawing a rectangle using pygame (W,H,L)
