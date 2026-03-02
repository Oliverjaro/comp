import math
import pygame
from constants import W, H, FPS, WHITE, GOLD, GRAY, GS, gen_upgrades, gen_background, load_high_scores, save_high_score
from player import Player
from worm import Worm


class Game:
    def __init__(self):
        pygame.init()
        self.scr = pygame.display.set_mode((W, H))
        pygame.display.set_caption("WormHunter")
        self.clk = pygame.time.Clock()
        self.f_s = pygame.font.SysFont("Arial", 20)
        self.f_m = pygame.font.SysFont("Arial", 36)
        self.f_l = pygame.font.SysFont("Arial", 72)
        self.bg = gen_background(W, H)
        self.state = GS.MENU
        self.score = 0
        self.player = Player()
        self.worm = Worm()
        self.bullets = []
        self.upg_opts = []
        self.upg_hi = 0
        self.hi_scores = load_high_scores()
        self._saved = False
        self.running = True

    def reset(self):
        self.score = 0
        self._saved = False
        self.player = Player()
        self.worm = Worm()
        self.bullets = []
        self.upg_opts = []
        self.upg_hi = 0
        self.state = GS.PLAYING

    def _txt(self, font, text, color, y):
        s = font.render(text, True, color)
        self.scr.blit(s, s.get_rect(centerx=W // 2, centery=y))

    def _save(self):
        if not self._saved:
            self.hi_scores = save_high_score(self.score); self._saved = True

    def _overlay(self, a=160):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, a))
        self.scr.blit(ov, (0, 0))

    def run(self):
        while self.running:
            dt = min(self.clk.tick(FPS) / 1000.0, 0.05)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN:
                    self._input(e.key)
            if self.state == GS.PLAYING:
                self._update(dt)
            self._draw(dt)
            pygame.display.flip()
        pygame.quit()

    def _input(self, key):
        if self.state == GS.MENU:
            if key == pygame.K_SPACE:
                self.reset()
        elif self.state == GS.UPGRADE:
            nums = {
                pygame.K_1: 0, pygame.K_KP1: 0,
                pygame.K_2: 1, pygame.K_KP2: 1,
                pygame.K_3: 2, pygame.K_KP3: 2,
            }
            if key in nums:
                self._pick(nums[key])
                return
            if key == pygame.K_UP:
                self.upg_hi = (self.upg_hi - 1) % len(self.upg_opts)
            elif key == pygame.K_DOWN:
                self.upg_hi = (self.upg_hi + 1) % len(self.upg_opts)
            elif key == pygame.K_RETURN:
                self._pick(self.upg_hi)
        elif self.state in (GS.OVER, GS.WIN):
            if key == pygame.K_r:
                self.reset()
            elif key == pygame.K_q:
                self.running = False

    def _pick(self, idx):
        if 0 <= idx < len(self.upg_opts):
            self.player.apply(self.upg_opts[idx])
            self.upg_opts = []
            self.upg_hi = 0
            self.state = GS.PLAYING

    def _update(self, dt):
        self.bullets.extend(self.player.update(dt, pygame.key.get_pressed()))
        for b in self.bullets:
            b.update(dt)
        self.bullets = [b for b in self.bullets if b.alive]
        self.worm.update(dt)
        self._collisions()
        if not self.worm.segs:
            self.state = GS.WIN
            self._save()

    def _collisions(self):
        to_rm, chests = [], []
        for b in self.bullets:
            if not b.alive:
                continue
            for si, seg in enumerate(self.worm.segs):
                if id(seg) in b.hit_segs or not seg.collides(b.rect): continue
                b.hit_segs.add(id(seg))
                if seg.hit(b.dmg):
                    self.score += 100
                    if seg.has_chest:
                        chests.append(seg.chest_tier)
                    if si not in to_rm:
                        to_rm.append(si)
                else:
                    self.score += 10
                b.pierc -= 1
                if b.pierc <= 0:
                    b.alive = False
                    break
        for i in sorted(to_rm, reverse=True):
            if i < len(self.worm.segs):
                self.worm.segs.pop(i)
        for i, s in enumerate(self.worm.segs):
            s.is_head = (i == 0)
        if chests and self.worm.segs:
            self.upg_opts = gen_upgrades(self.player, chests[0])
            self.upg_hi = 0
            self.state = GS.UPGRADE
        if self.state == GS.PLAYING:
            hb = self.player.rect.inflate(-10, -10)
            for seg in self.worm.segs:
                if seg.hit_rect.colliderect(hb):
                    self.state = GS.OVER
                    self._save()
                    break

    def _draw(self, dt):
        self.scr.blit(self.bg, (0, 0))
        if self.state == GS.MENU:
            self._draw_menu()
        elif self.state in (GS.PLAYING, GS.UPGRADE):
            self._draw_play(dt)
            self._draw_hud()
            if self.state == GS.UPGRADE:
                self._draw_upg()
        elif self.state in (GS.OVER, GS.WIN):
            self._draw_play(dt)
            if self.state == GS.OVER:
                self._draw_end("GAME OVER", (255, 50, 50))
            else:
                self._draw_end("VICTORY!", (50, 255, 50), "You destroyed the worm!")

    def _draw_play(self, dt):
        self.worm.draw(self.scr, dt)
        for b in self.bullets:
            b.draw(self.scr)
        self.player.draw(self.scr)

