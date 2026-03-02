"""Shared constants, helpers, and enums for WormHunter."""
import os, json, enum, random, pygame
#Screen Dimensions and performance setting
W, H, FPS = 600, 800, 60
COLOR_BG = (10, 10, 20)
PLAYER_SPEED, BULLET_SPEED, BASE_CD = 300, 500, 300 #Player and bullet default settings
WORM_SPD, WORM_SPD_FRENZY = 160, 340 #Worm movement speeds (normal v frenzy)
FRENZY_INTERVAL, FRENZY_DUR = 12.0, 3.5 #Sets when the frenzy mode happens in seconds
DROP_AMT, SEG_SPACE, SEG_COUNT, EDGE_M = 70, 38, 120, 40 #Segments and drop-related constants
SEG_W, SEG_H = 40, 40
HP_BASE, HP_PER, HP_BOOST, HP_STEP_Y = 1, 0.35, 3.0, 80 #Worm health and difficulty scaling
CHEST_CHANCE, CHEST_HI = 0.10, 0.35 #Chest drop chance (default and enhanced)
GAME_DIR = os.path.dirname(os.path.abspath(__file__))
SCORE_FILE = os.path.join(GAME_DIR, "wormhunter_scores.json") #Paths for game assets and save files.
WHITE, GOLD, GRAY = (255, 255, 255), (255, 215, 0), (200, 200, 200)

clamp = lambda v, lo, hi: max(lo, min(hi, v)) #Clamps a value between two bounds


def _load_sprite(name, size): #Loads an image from disk and scale it smoothly.
    try:
        img = pygame.image.load(os.path.join(GAME_DIR, name)).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    except (pygame.error, FileNotFoundError):
        return None #Returns none if the sprite is missing or it fails to load.


def load_high_scores(): #Loads the top 5 high scores from a JSON file.
    try:
        with open(SCORE_FILE, "r") as f:
            d = json.load(f) #Validate and sort, only keep numeric list entries.
            return sorted(d, reverse=True)[:5] if isinstance(d, list) else []
    except Exception: #If the file doesn't exist or corrupt then it returns empty.
        return []


def save_high_score(score): #Save a new score into the hig score list, only keeping the top 5.
    s = sorted(load_high_scores() + [score], reverse=True)[:5]
    try:
        with open(SCORE_FILE, "w") as f:
            json.dump(s, f)
    except OSError: #Fails silently if saving encounters an error.
        pass
    return s


def gen_background(w, h): #Generate a static starfield/grid background surface.
    surf = pygame.Surface((w, h))
    surf.fill(COLOR_BG)
    for gx in range(0, w, 50):
        pygame.draw.line(surf, (25, 25, 40), (gx, 0), (gx, h))
    for gy in range(0, h, 50):
        pygame.draw.line(surf, (25, 25, 40), (0, gy), (w, gy))
    for _ in range(120):
        b = random.randint(100, 255)
        surf.set_at((random.randint(0, w - 1), random.randint(0, h - 1)), (b, b, b))
    return surf.convert()


class GS(enum.Enum): #Game states for main loop control/
    MENU = 0
    PLAYING = 1
    UPGRADE = 2
    OVER = 3
    WIN = 4


class UT(enum.Enum):
    HEAVY = "Heavy Rounds (3x dmg)"


def gen_upgrades(p, tier): 
    pool = list(UT)
    for attr, ut in [
        ("double_shot", UT.DOUBLE), ("spread_shot", UT.SPREAD),
        ("power_shot", UT.POWER), ("mega_spread", UT.MEGA),
        ("heavy_rounds", UT.HEAVY), ("bullet_storm", UT.STORM),
    ]:
        if getattr(p, attr):
            pool = [u for u in pool if u != ut]
    if not p.spread_shot:
        pool = [u for u in pool if u != UT.MEGA]
    if not p.power_shot:
        pool = [u for u in pool if u != UT.HEAVY]
    if tier == "high":
        for s in (UT.POWER, UT.PIERCE, UT.HEAVY, UT.MEGA, UT.STORM):
            if s in pool:
                pool.append(s)
    return random.sample(pool, min(3, len(pool))) if pool else [UT.RAPID]
