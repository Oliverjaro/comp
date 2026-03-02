"""Worm segment entity."""
import math, random
import pygame
from constants import SEG_W, SEG_H, HP_BASE, HP_BOOST, WHITE, GOLD, clamp, _load_sprite


class Segment: #Class-level flags and colours shared across all segments
    _loaded = False
    _col_calm = (210, 170, 110)
    _col_frenzy = (220, 70, 50)

    def __init__(self, x, y, hp, is_head=False): 
        #Logical position of the segment
        self.x, self.y = float(x), float(y)
        self.is_head = is_head
        
        #Health and scaling properties
        self.max_hp = self.hp = hp
        
        #Chest drop flags
        self.has_chest = False
        self.chest_tier = "normal"
        
        #Short flash timer after being hit
        self.flash = 0.0
       
        #Per segment phase for wobble animation
        self._phase = random.uniform(0, 2 * math.pi)

        #Collision rect for hits with bullets/player
        self.hit_rect = pygame.Rect(0, 0, SEG_W, SEG_H)
        self.hit_rect.center = (int(x), int(y))

    def scale_hp(self, plvl):
        #Increase HP based on player level/progrression
        want = int(HP_BASE + HP_BOOST * plvl)
        if want > self.max_hp:
            bump = want - self.max_hp
            self.max_hp = want
            self.hp = min(self.max_hp, self.hp + max(1, bump // 2))

    def hit(self, dmg):
        #Apply damage and trigger a brief flash; returns True if killed
        self.hp -= dmg
        self.flash = 0.15
        return self.hp <= 0

    def collides(self, r):
        #Checks collision with a slightly inflated hitbox
        return self.hit_rect.inflate(6, 6).colliderect(r)

    @classmethod
    def _init_sprites(cls):
        #Lazy-load segment sprites and font once
        if cls._loaded: return
        cls._loaded = True
        cls._font = pygame.font.SysFont("consolas", 15, bold=True)
        dim = SEG_W + 10
        cls._spr_calm = _load_sprite("wormcalm.png", (dim, dim))
        cls._spr_angry = _load_sprite("wormangry.png", (dim, dim))

    def draw(self, surf, dt, nxt=None, frenzy=False):
        #Render the segment (head/body, HP text, and chest icon)
        Segment._init_sprites()
        hpct = clamp(self.hp / max(1, self.max_hp), 0.0, 1.0)
        wobble = math.sin(pygame.time.get_ticks() / 1000.0 * 2.5 + self._phase)
        cx, cy = int(self.x), int(self.y)
        base_col = self._col_frenzy if frenzy else self._col_calm
        radius = (SEG_W + 10) // 2 if self.is_head else max(8, int(SEG_W // 2 + wobble)) #Head radius is fixed, body wobbles slightly.
        # Joint dot
        if nxt:
            jc = tuple(max(0, c - 30) for c in base_col)
            pygame.draw.circle(surf, jc,
                               (int((self.x + nxt.x) / 2), int((self.y + nxt.y) / 2)),
                               max(5, SEG_W // 4))
        # Head sprite or fallback circle
        if self.is_head:
            spr = (self._spr_angry if frenzy else None) or self._spr_calm
            if spr and self.flash <= 0:
                img = spr
                if hpct < 0.95:
                    d = int(255 * (0.55 + 0.45 * hpct))
                    tint = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                    tint.fill((d, d, d, 0))
                    img = img.copy()
                    img.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                surf.blit(img, img.get_rect(center=(cx, cy)))
            else:
                pygame.draw.circle(surf, WHITE if self.flash > 0 else base_col, (cx, cy), radius)
        # Body circle
        else:
            col = tuple(int(c * (0.55 + 0.45 * hpct)) for c in base_col)
            if self.flash > 0:
                pygame.draw.circle(surf, WHITE, (cx, cy), radius)
            else:
                pygame.draw.circle(surf, col, (cx, cy), radius)
                pygame.draw.circle(surf, tuple(max(0, c - 50) for c in col), (cx, cy), max(3, radius - 3))
                pygame.draw.circle(surf, tuple(min(255, c + 70) for c in col),
                                   (cx - radius // 3, cy - radius // 3), max(2, radius // 4))
        # HP number
        hc = WHITE if hpct > 0.6 else (255, 255, 100) if hpct > 0.3 else (255, 80, 80)
        txt = self._font.render(str(self.hp), True, hc)
        surf.blit(txt, txt.get_rect(center=(cx, cy + 1)))
        # Chest icon
        if self.has_chest:
            cc = (150, 0, 255) if self.chest_tier == "high" else (0, 100, 255)
            cr = pygame.Rect(cx - 7, cy - radius - 11, 14, 9)
            pygame.draw.rect(surf, cc, cr, border_radius=2)
            pygame.draw.rect(surf, GOLD, cr, width=1, border_radius=2)
            pygame.draw.rect(surf, GOLD, pygame.Rect(cx - 2, cy - radius - 8, 4, 4))
        self.flash = max(0.0, self.flash - dt)

