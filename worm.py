"""Worm entity — head + body segments with trail-follow movement."""
import math, random
import pygame
from constants import (W, SEG_COUNT, SEG_SPACE, HP_BASE, HP_PER, HP_STEP_Y, HP_BOOST,
                       WORM_SPD, WORM_SPD_FRENZY, FRENZY_INTERVAL, FRENZY_DUR,
                       EDGE_M, DROP_AMT, CHEST_CHANCE, CHEST_HI, clamp)
from segment import Segment
 
 
class Worm:
    def __init__(self):
        # Segment list (head at index 0)
        self.segs = []
 
        # Movement and speed parameters
        self.spd = self.base_spd = float(WORM_SPD)
        self.dir = 1          # horizontal direction: 1 = right, -1 = left
        self.hvx = float(WORM_SPD)  # smoothed horizontal velocity
 
        # Progression level and next Y threshold for scaling
        self.plvl = 0
        self._next_y = 50.0 + HP_STEP_Y
 
        # Vertical drop interpolation state
        self._drop_tgt = self._drop_cur = 0.0
 
        # Frenzy mode control
        self.frenzy = False
        self._fr_timer = 0.0
        self._fr_cd = FRENZY_INTERVAL
 
        # Trail of past head positions for body following
        self._trail = []
 
        # Build initial worm configuration
        self._build()
 
    def _build(self):
        """Create initial segments, trail, and chest distribution."""
        sx, sy = float(W // 2), 60.0
 
        # Create head + body segments with increasing base HP
        self.segs = [
            Segment(sx, sy, max(1, int(HP_BASE + i * HP_PER)), i == 0)
            for i in range(SEG_COUNT)
        ]
 
        # Pre-fill trail with a flat horizontal line behind the head
        self._trail = [
            (sx - p * 2.0, sy)
            for p in range(SEG_SPACE * (SEG_COUNT + 4) // 2 + 1)
        ]
 
        # Place body segments along the trail
        self._place_bodies()
 
        # Evenly-spaced chest segments with a bit of random jitter
        nc = max(1, int(SEG_COUNT * CHEST_CHANCE))
        sp = (SEG_COUNT - 1) / (nc + 1)
        for k in range(1, nc + 1):
            j = random.randint(-max(1, int(sp * 0.25)), max(1, int(sp * 0.25)))
            i = clamp(int(sp * k) + j, 1, SEG_COUNT - 1)
            if i < len(self.segs):
                self.segs[i].has_chest = True
                self.segs[i].chest_tier = "high" if random.random() < CHEST_HI else "normal"
 
    def _sample(self, dist):
        """Find the point at cumulative distance `dist` along the head trail."""
        if not self._trail or dist <= 0:
            return self._trail[0] if self._trail else (float(W // 2), 60.0)
 
        d = 0.0
        for i in range(1, len(self._trail)):
            ax, ay = self._trail[i - 1]
            bx, by = self._trail[i]
            seg_len = math.hypot(bx - ax, by - ay)
 
            # If the target distance lies within this segment, interpolate
            if d + seg_len >= dist:
                t = (dist - d) / seg_len if seg_len > 0.0001 else 0.0
                return (ax + (bx - ax) * t, ay + (by - ay) * t)
 
            d += seg_len
 
        # If dist is beyond the end, return last point
        return self._trail[-1]
 
    def _place_bodies(self):
        """Position all body segments along the trail at fixed spacing."""
        for i in range(1, len(self.segs)):
            px, py = self._sample(i * SEG_SPACE)
            s = self.segs[i]
            s.x, s.y = px, py
            s.hit_rect.center = (int(px), int(py))
 
    def update(self, dt):
        """Update movement, frenzy, trail, and segment positions."""
        if not self.segs:
            return
 
        head = self.segs[0]
 
        # Frenzy state: toggles between normal and high-speed modes
        if self.frenzy:
            self._fr_timer -= dt
            if self._fr_timer <= 0:
                self.frenzy = False
                self._fr_cd = FRENZY_INTERVAL
                self.spd = self.base_spd
        else:
            self._fr_cd -= dt
            if self._fr_cd <= 0:
                self.frenzy = True
                self._fr_timer = FRENZY_DUR
                self.spd = WORM_SPD_FRENZY
 
        # Ensure head flag is accurate
        for i, s in enumerate(self.segs):
            s.is_head = (i == 0)
 
        # Smooth horizontal movement towards desired speed in current direction
        self.hvx += (self.spd * self.dir - self.hvx) * min(1.0, 8 * dt)
 
        # Bounce at screen edges and trigger downward drop
        if (head.x <= EDGE_M and self.dir == -1) or (head.x >= W - EDGE_M and self.dir == 1):
            self.dir *= -1
            self._drop_tgt += DROP_AMT
 
        # Ease vertical drop towards drop target
        dd = self._drop_tgt - self._drop_cur
        if abs(dd) > 0.1:
            step = dd * 4.0 * dt
            self._drop_cur += step
            head.y += step
        else:
            self._drop_cur = self._drop_tgt
 
        # Apply horizontal movement and subtle sinusoidal bobbing
        head.x = clamp(head.x + self.hvx * dt, float(EDGE_M), float(W - EDGE_M))
        head.y += math.sin(pygame.time.get_ticks() / 1000.0 * 1.8) * 0.3
        head.hit_rect.center = (int(head.x), int(head.y))
 
        # Progress-based difficulty scaling as the worm descends
        if head.y >= self._next_y:
            self.plvl += 1
            self._next_y += HP_STEP_Y
            self.base_spd += 6.0
            if not self.frenzy:
                self.spd = self.base_spd
 
        # Record new head position into the trail when far enough from last point
        if self._trail:
            lx, ly = self._trail[0]
            if math.hypot(head.x - lx, head.y - ly) >= 2.0:
                self._trail.insert(0, (head.x, head.y))
                # Keep trail bounded to what segments actually need
                max_pts = SEG_SPACE * (len(self.segs) + 4) // 2 + 50
                if len(self._trail) > max_pts:
                    self._trail = self._trail[:max_pts]
        else:
            self._trail = [(head.x, head.y)]
 
        # Body segments follow the trail with smoothing and scale HP with progress
        for i in range(1, len(self.segs)):
            s = self.segs[i]
            tx, ty = self._sample(i * SEG_SPACE)
            lr = min(1.0, 18.0 * dt)
            s.x += (tx - s.x) * lr
            s.y += (ty - s.y) * lr
            s.hit_rect.center = (int(s.x), int(s.y))
            s.scale_hp(self.plvl)
 
    def draw(self, surf, dt):
        """Draw worm segments back to front, passing next segment for joints."""
        for i in range(len(self.segs) - 1, -1, -1):
            nxt = self.segs[i + 1] if i + 1 < len(self.segs) else None
            self.segs[i].draw(surf, dt, nxt, self.frenzy)
