"""Worm segment entity."""
import math, random
import pygame
from constants import SEG_W, SEG_H, HP_BASE, HP_BOOST, WHITE, GOLD, clamp, _load_sprite

pygame.init()
pygame.mixer.init()

damage_sound = pygame.mixer.Sound("damage.mp3")
damage_sound.set_volume(0.5)
class Segment:
    _loaded = False
    _col_calm = (210, 170, 110)
    _col_frenzy = (220, 70, 50)

    def __init__(self, x, y, hp, is_head=False):
        self.x, self.y = float(x), float(y)
        self.is_head = is_head
        self.max_hp = self.hp = hp
        self.has_chest = False
        self.chest_tier = "normal"
        self.flash = 0.0
        self._phase = random.uniform(0, 2 * math.pi)
        self.hit_rect = pygame.Rect(0, 0, SEG_W, SEG_H)
        self.hit_rect.center = (int(x), int(y))

    def scale_hp(self, plvl):
        want = int(HP_BASE + HP_BOOST * plvl)
        if want > self.max_hp:
            bump = want - self.max_hp
            self.max_hp = want
            self.hp = min(self.max_hp, self.hp + max(1, bump // 2))

    def hit(self, dmg):
        self.hp -= dmg
        self.flash = 0.15
        damage_sound.play() 
        return self.hp <= 0


        
    def collides(self, r):
        return self.hit_rect.inflate(6, 6).colliderect(r)

    @classmethod
    def _init_sprites(cls):
        if cls._loaded: return
        cls._loaded = True
        cls._font = pygame.font.SysFont("consolas", 15, bold=True)
        dim = SEG_W + 10
        cls._spr_calm = _load_sprite("wormcalm.png", (dim, dim))
        cls._spr_angry = _load_sprite("wormangry.png", (dim, dim))
        cls.spr_body = _load_sprite("wormbody.png", (dim,dim))

    def draw(self, surf, dt, nxt=None, frenzy=False):
        Segment._init_sprites()
        hpct = clamp(self.hp / max(1, self.max_hp), 0.0, 1.0)
        wobble = math.sin(pygame.time.get_ticks() / 1000.0 * 2.5 + self._phase)
        cx, cy = int(self.x), int(self.y)
        base_col = self._col_frenzy if frenzy else self._col_calm
        radius = (SEG_W + 10) // 2 if self.is_head else max(8, int(SEG_W // 2 + wobble))
        # Joint dot
        if nxt:
            jc = tuple(max(0, c - 30) for c in base_col)
            pygame.draw.circle(surf, jc,
                               (int((self.x + nxt.x) / 2), int((self.y + nxt.y) / 2)),
                               max(5, SEG_W // 4))
        # Head sprite or body sprite
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
            spr1 = self.spr_body
            if spr1 and self.flash <= 0:
                img = spr1
                if hpct < 0.95:
                    d = int(255 * (0.55 + 0.45 * hpct))
                    tint = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                    tint.fill((d, d, d, 0))
                    img = img.copy()
                    img.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                surf.blit(img, img.get_rect(center=(cx, cy)))
                
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
