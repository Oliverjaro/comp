"""Player entity."""
import pygame
from constants import W, H, PLAYER_SPEED, BASE_CD, WHITE, UT, clamp, _load_sprite
from bullet import Bullet


class Player:
    _sprite = None
    _loaded = False

    def __init__(self):
        self.w, self.h = 40, 40
        self.x, self.y = float(W // 2), float(H - 60)
        self.rect = pygame.Rect(0, 0, self.w, self.h)
        self._sync()
        self.rapid_fire_level = self.piercing_level = 0
        self.double_shot = self.spread_shot = self.power_shot = False
        self.mega_spread = self.bullet_storm = self.heavy_rounds = False
        self.timer = 0.0

    def _sync(self):
        self.rect.center = (int(self.x), int(self.y))

    def cooldown(self):
        cd = BASE_CD * (0.6 ** self.rapid_fire_level)
        if self.bullet_storm:
            cd *= 0.4
        if self.power_shot:
            cd *= 1.3
        if self.heavy_rounds:
            cd *= 1.2
        return max(40.0, cd)

    def apply(self, ut):
        if ut == UT.RAPID: self.rapid_fire_level += 1
        elif ut == UT.PIERCE: self.piercing_level += 1
        elif ut == UT.DOUBLE: self.double_shot = True
        elif ut == UT.SPREAD: self.spread_shot = True
        elif ut == UT.POWER: self.power_shot = True
        elif ut == UT.MEGA: self.mega_spread = True
        elif ut == UT.STORM: self.bullet_storm = True
        elif ut == UT.HEAVY: self.heavy_rounds = True

    def shoot(self):
        cx, cy = float(self.rect.centerx), float(self.rect.top)
        dmg = (5 if self.heavy_rounds and self.power_shot
               else 3 if self.heavy_rounds
               else 2 if self.power_shot else 1)
        p = 1 + self.piercing_level
        if self.mega_spread:
            return [Bullet(cx, cy, a, dmg, p) for a in (-25, -12, 0, 12, 25)]
        if self.spread_shot:
            return [Bullet(cx, cy, a, dmg, p) for a in (-15, 0, 15)]
        if self.double_shot:
            return [Bullet(cx - 8, cy, 0, dmg, p), Bullet(cx + 8, cy, 0, dmg, p)]
        return [Bullet(cx, cy, 0, dmg, p)]

    def update(self, dt, keys):
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += PLAYER_SPEED
        self.x = clamp(self.x + dx * dt, self.w / 2, W - self.w / 2)
        self._sync()
        self.timer -= dt * 1000
        if self.timer <= 0:
            self.timer = self.cooldown()
            return self.shoot()
        return []

    def draw(self, s):
        if not Player._loaded:
            Player._loaded = True
            Player._sprite = _load_sprite("player 1.png", (self.w, self.h))
        if Player._sprite:
            s.blit(Player._sprite, Player._sprite.get_rect(center=self.rect.center))
        else:
            pygame.draw.rect(s, WHITE, self.rect)
