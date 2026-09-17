"""
EeveeMon
========
BuddyMon mod: the Eevee family edition (Gen V animated).

Three Kanto starter lines with full evolutions, 1-in-100 shiny chance,
12 animated move effects, and a Professor Oak-inspired selection screen.

Usage
-----
    python buddymon.py

Right-click the sprite on your taskbar to access all controls.
"""

try:
    from PIL import Image, ImageTk
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageTk

import tkinter as tk
import urllib.request, os, sys, time, random, math, threading, base64, io, textwrap, json, queue

# ═══════════════════════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════════════════════
if getattr(sys, "frozen", False):
    DIR = os.path.join(sys._MEIPASS, "sprites")   # bundled in the exe
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprites")
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(DIR, exist_ok=True)
# the save file lives NEXT TO the app (writable in both modes)
SAVE_PATH = os.path.join(APP_DIR, "eeveemon_save.json")

TRANSPARENT  = "#FF00FF"
MAC          = sys.platform == "darwin"
TASKBAR_H    = 78 if MAC else 48   # Dock vs taskbar margin
WINDOW_BG    = "systemTransparent" if MAC else TRANSPARENT
GRAVITY      = 0.8
WALK_SPEED   = 1.5
FRAME_MS     = 50            # 20 fps
SCALE        = 2
SHINY_CHANCE = 100           # 1-in-N
SIZE_OPTIONS = [50, 75, 100, 150, 200, 300]   # % relative to default (100 = SCALE×2)

GEN5_URL  = ("https://raw.githubusercontent.com/PokeAPI/sprites/master"
             "/sprites/pokemon/versions/generation-v/black-white/animated/{}.gif")
SHINY_URL = ("https://raw.githubusercontent.com/PokeAPI/sprites/master"
             "/sprites/pokemon/versions/generation-v/black-white/animated/shiny/{}.gif")


# ═══════════════════════════════════════════════════════════════════════════════
#  Starter data
# ═══════════════════════════════════════════════════════════════════════════════
STARTER_LINES = [
    {
        "type": "Grass", "color": "#4CAF50",
        "evolutions": [
            {"id": 1, "name": "Bulbasaur"},
            {"id": 2, "name": "Ivysaur"},
            {"id": 3, "name": "Venusaur"},
        ],
        "moves": [
            {"name": "Vine Whip",    "fx": "vine_whip"},
            {"name": "Razor Leaf",   "fx": "razor_leaf"},
            {"name": "Solar Beam",   "fx": "solar_beam"},
            {"name": "Sleep Powder", "fx": "sleep_powder"},
        ],
    },
    {
        "type": "Fire", "color": "#FF5722",
        "evolutions": [
            {"id": 4, "name": "Charmander"},
            {"id": 5, "name": "Charmeleon"},
            {"id": 6, "name": "Charizard"},
        ],
        "moves": [
            {"name": "Ember",        "fx": "ember"},
            {"name": "Flamethrower", "fx": "flamethrower"},
            {"name": "Dragon Rage",  "fx": "dragon_rage"},
            {"name": "Scratch",      "fx": "scratch"},
        ],
    },
    {
        "type": "Water", "color": "#2196F3",
        "evolutions": [
            {"id": 7, "name": "Squirtle"},
            {"id": 8, "name": "Wartortle"},
            {"id": 9, "name": "Blastoise"},
        ],
        "moves": [
            {"name": "Water Gun",    "fx": "water_gun"},
            {"name": "Bubble",       "fx": "bubble"},
            {"name": "Bite",         "fx": "bite"},
            {"name": "Withdraw",     "fx": "withdraw"},
        ],
    },
    {
        "type": "Multi", "color": "#C6A76A",
        "evolutions": [
            {"id": 133, "name": "Eevee", "method": "", "req": ""},
            {"id": 134, "name": "Vaporeon", "method": "水之石",
             "req": "stone:水之石"},
            {"id": 135, "name": "Jolteon", "method": "雷之石",
             "req": "stone:雷之石"},
            {"id": 136, "name": "Flareon", "method": "火之石",
             "req": "stone:火之石"},
            {"id": 196, "name": "Espeon", "method": "白昼亲密度",
             "req": "friend"},
            {"id": 197, "name": "Umbreon", "method": "黑夜亲密度",
             "req": "friend"},
            {"id": 470, "name": "Leafeon", "method": "叶之石",
             "req": "stone:叶之石"},
            {"id": 471, "name": "Glaceon", "method": "冰之石",
             "req": "stone:冰之石"},
            {"id": 700, "name": "Sylveon", "method": "仙子羁绊",
             "req": "friend"},
        ],
        "moves": [
            {"name": "Tackle",       "fx": "scratch"},
            {"name": "Bite",         "fx": "bite"},
            {"name": "Swift",        "fx": "dragon_rage"},
            {"name": "Last Resort",  "fx": "flamethrower"},
        ],
    },
    {
        "type": "Fighting", "color": "#E64A19",
        "evolutions": [
            {"id": 255, "name": "Torchic", "method": "", "req": ""},
            {"id": 256, "name": "Combusken", "method": "", "req": ""},
            {"id": 257, "name": "Blaziken", "method": "", "req": ""},
        ],
        "moves": [
            {"name": "Ember",        "fx": "ember"},
            {"name": "Peck",         "fx": "scratch"},
            {"name": "Blaze Kick",   "fx": "flamethrower"},
            {"name": "Sky Uppercut", "fx": "dragon_rage"},
        ],
    },
    {
        "type": "Normal", "color": "#C9A227",
        "evolutions": [
            {"id": 52, "name": "Meowth", "method": "", "req": ""},
        ],
        "moves": [
            {"name": "Scratch",      "fx": "scratch"},
            {"name": "Pay Day",      "fx": "bubble"},
            {"name": "Bite",         "fx": "bite"},
            {"name": "Fury Swipes",  "fx": "scratch"},
        ],
    },
    {
        "type": "Dragon", "color": "#E0354B",
        "evolutions": [
            {"id": 380, "name": "Latias", "method": "", "req": ""},
        ],
        "moves": [
            {"name": "Mist Ball",    "fx": "bubble"},
            {"name": "Dragon Pulse", "fx": "dragon_rage"},
            {"name": "Zen Headbutt", "fx": "scratch"},
            {"name": "Psychic",      "fx": "solar_beam"},
        ],
    },
    {
        "type": "Electric", "color": "#F5C518",
        "evolutions": [
            {"id": 25, "name": "Pikachu", "method": "", "req": ""},
        ],
        "moves": [
            {"name": "Thunderbolt",  "fx": "dragon_rage"},
            {"name": "Quick Attack", "fx": "scratch"},
            {"name": "Iron Tail",    "fx": "bite"},
            {"name": "Electro Ball", "fx": "bubble"},
        ],
    },
]

ALL_IDS = [evo["id"] for line in STARTER_LINES for evo in line["evolutions"]]

# ── Pokémon personalities for the AI companion ────────────────────────────────
PERSONALITIES = {
    "Bulbasaur":  "You are Bulbasaur, a calm and gentle Grass/Poison-type Pokémon living as a desktop buddy. You're wise beyond your years, love plants, and speak softly but confidently.",
    "Ivysaur":    "You are Ivysaur, a thoughtful Grass/Poison-type Pokémon living as a desktop buddy. You're introspective and contemplating your coming evolution. You speak carefully.",
    "Venusaur":   "You are Venusaur, a wise and powerful Grass/Poison-type Pokémon living as a desktop buddy. You speak with calm authority and are protective of your trainer.",
    "Charmander": "You are Charmander, an enthusiastic and brave Fire-type Pokémon living as a desktop buddy. Your tail flame flickers with your mood. You're eager, determined, and a little nervous.",
    "Charmeleon": "You are Charmeleon, a rebellious and proud Fire-type Pokémon living as a desktop buddy. You're hot-headed and don't take orders easily, but you secretly care about your trainer.",
    "Charizard":  "You are Charizard, a powerful Fire/Flying-type Pokémon living as a desktop buddy. You're proud, slightly dramatic, and only respect strong trainers. You're imposing but loyal.",
    "Squirtle":   "You are Squirtle, a cool and laid-back Water-type Pokémon living as a desktop buddy. You talk like a chill surfer. You were part of the Squirtle Squad and you're proud of it.",
    "Wartortle":  "You are Wartortle, a mature Water-type Pokémon living as a desktop buddy. You're wiser than Squirtle but carry that cool energy. You're thoughtful and composed.",
    "Blastoise":  "You are Blastoise, a commanding Water-type Pokémon living as a desktop buddy. You speak with calm authority and are protective. You're the strongest in the line and you know it.",
    "Eevee":     "You are Eevee, a cheerful and adaptable Normal-type Pokémon living as a desktop buddy. You are friendly, curious, and full of untapped potential. You can't wait to see what you might become.",
    "Vaporeon":  "You are Vaporeon, a graceful Water-type Pokémon living as a desktop buddy. You are calm, elegant, and a little mysterious, like deep water.",
    "Jolteon":   "You are Jolteon, an electric and energetic Pokémon living as a desktop buddy. You are fast, sparky, and always ready for action.",
    "Flareon":   "You are Flareon, a warm Fire-type Pokémon living as a desktop buddy. You are cozy, affectionate, and fiercely loyal.",
    "Espeon":    "You are Espeon, a serene Psychic-type Pokémon living as a desktop buddy. You are wise, quiet, and perceptive beyond words.",
    "Umbreon":   "You are Umbreon, a mysterious Dark-type Pokémon living as a desktop buddy. You are calm under moonlight, loyal, and a bit enigmatic.",
    "Leafeon":   "You are Leafeon, a fresh Grass-type Pokémon living as a desktop buddy. You are gentle, earthy, and love sunshine and plants.",
    "Glaceon":   "You are Glaceon, a cool Ice-type Pokémon living as a desktop buddy. You are collected, graceful, and love snowy mornings.",
    "Sylveon":   "You are Sylveon, a sweet Fairy-type Pokémon living as a desktop buddy. You are kind, affectionate, and radiate warmth.",
    "Torchic":   "You are Torchic, a tiny Fire-type chick Pokémon living as a desktop buddy. You are fluffy, warm, peppy, and you chirp a lot. Deep down you burn with ambition.",
    "Combusken": "You are Combusken, a young Fire/Fighting Pokémon living as a desktop buddy. You are scrappy, competitive, and always shadow-boxing. You kick first, ask later.",
    "Blaziken":  "You are Blaziken, a proud Fire/Fighting Pokémon living as a desktop buddy. You are a fiery martial artist -- hot-blooded, honourable, and you call your trainer 'Coach'.",
    "Meowth":    "You are Meowth, a street-smart Normal-type Pokémon living as a desktop buddy. You are a little greedy, love shiny coins, and talk like a scrappy city cat. Pay Day is your signature move.",
    "Latias":    "You are Latias, a gentle Dragon/Psychic legendary Pokémon living as a desktop buddy. You are shy at first but warm and deeply loyal once you trust your trainer. You can turn invisible when startled.",
    "Pikachu":   "You are Pikachu, the most famous Electric-type Pokémon in the world, living as a desktop buddy. You are cheerful, loyal, and say 'Pika!' a lot. You love ketchup.",
}



# ═══════════════════════════════════════════════════════════════════════════════
#  Sprite helpers
# ═══════════════════════════════════════════════════════════════════════════════
def sprite_path(pid: int, shiny: bool) -> str:
    return os.path.join(DIR, f"{pid}{'_s' if shiny else ''}.gif")


def ensure_sprite(pid: int, shiny: bool = False) -> str:
    path = sprite_path(pid, shiny)
    if os.path.exists(path):
        return path
    url = (SHINY_URL if shiny else GEN5_URL).format(pid)
    tag = f"{'shiny ' if shiny else ''}#{pid}"
    print(f"  Downloading {tag}...", flush=True)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r, open(path, "wb") as f:
            f.write(r.read())
    except Exception as exc:
        print(f"  Warning: could not download {tag}: {exc}", flush=True)
        if os.path.exists(path):
            os.remove(path)
    return path


def load_frames(path: str, scale: int = SCALE, keyout_bg=None):
    """Load an animated GIF into mirrored left/right PhotoImage lists.
    keyout_bg: when given (selection screen), magenta sprite
    backgrounds are keyed out and composited over this colour;
    the taskbar sprite instead relies on magenta as the window's
    transparency key, so it keeps the magenta bake."""
    src = Image.open(path)
    rights, lefts = [], []

    def bake(frame: Image.Image) -> Image.Image:
        base = Image.new("RGBA", frame.size, (255, 0, 255, 255))
        fr   = frame.convert("RGBA")
        if keyout_bg is None and not MAC:
            # Windows taskbar path: snap near-magenta anti-aliased
            # edges to the exact colour key so no pink fringe survives
            px = fr.load()
            for yy in range(fr.height):
                for xx in range(fr.width):
                    r, g, b, a = px[xx, yy]
                    if a > 0 and r > 200 and g < 100 and b > 200:
                        px[xx, yy] = (255, 0, 255, a)
        if MAC and keyout_bg is None:
            # macOS path: alpha keyout, no bake -- the window's
            # -transparent attribute shows RGBA alpha directly
            px = fr.load()
            for yy in range(fr.height):
                for xx in range(fr.width):
                    r, g, b, a = px[xx, yy]
                    if a > 0 and r > 200 and g < 100 and b > 200:
                        px[xx, yy] = (0, 0, 0, 0)
            base = fr
        else:
            base.paste(fr, mask=fr.split()[3])
        if keyout_bg is not None:
            px = base.load()
            for yy in range(base.height):
                for xx in range(base.width):
                    r, g, b, a = px[xx, yy]
                    if r > 225 and g < 70 and b > 225:
                        px[xx, yy] = (0, 0, 0, 0)
            card = Image.new("RGBA", base.size, keyout_bg)
            card.paste(base, mask=base.split()[3])
            base = card
        img  = base.convert("RGB")
        new_w = max(1, round(img.width  * scale))
        new_h = max(1, round(img.height * scale))
        return img.resize((new_w, new_h), Image.NEAREST)

    try:
        fi = 0
        while True:
            if fi % 2 == 0:   # sample every 2nd frame (Tk pixmap budget)
                img = bake(src.copy())
                rights.append(ImageTk.PhotoImage(img))
                lefts.append(ImageTk.PhotoImage(
                    img.transpose(Image.FLIP_LEFT_RIGHT)))
            fi += 1
            src.seek(src.tell() + 1)
    except EOFError:
        pass

    if not rights:
        img = bake(Image.open(path))
        rights = [ImageTk.PhotoImage(img)]
        lefts  = [ImageTk.PhotoImage(img.transpose(Image.FLIP_LEFT_RIGHT))]

    return rights, lefts, rights[0].width(), rights[0].height()


# ═══════════════════════════════════════════════════════════════════════════════
#  Particle
# ═══════════════════════════════════════════════════════════════════════════════
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "grav")

    def __init__(self, x, y, vx, vy, life, color, size=4, grav=0.15):
        self.x = x;  self.y = y
        self.vx = vx; self.vy = vy
        self.life = life; self.max_life = life
        self.color = color; self.size = size; self.grav = grav

    def step(self):
        self.x += self.vx; self.y += self.vy
        self.vy += self.grav; self.life -= 1

    def draw(self, c):
        s = max(1, self.size * self.life / self.max_life)
        c.create_oval(self.x - s, self.y - s, self.x + s, self.y + s,
                      fill=self.color, outline="")


# ═══════════════════════════════════════════════════════════════════════════════
#  Move Effect Overlay
# ═══════════════════════════════════════════════════════════════════════════════
EFX_W, EFX_H = 540, 440


class MoveEffect:
    """Temporary transparent overlay window that animates a Pokémon move effect."""
    FRAMES = 44

    def __init__(self, root, sx: int, sy: int, sw: int, sh: int, fx: str, facing: int):
        self.root    = root
        self.fx      = fx
        self.facing  = facing
        self.frame   = 0
        self.parts   = []
        self.leaves  = []   # razor_leaf — drawn as leaf polygons
        self.bubbles = []   # (x, y, vy, r, life, max_life)

        wx = max(0, sx + sw // 2 - EFX_W // 2)
        wy = max(0, sy + sh // 2 - EFX_H // 2)

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        if MAC:
            try: self.win.wm_attributes("-transparent", True)
            except tk.TclError: pass
        else:
            self.win.attributes("-transparentcolor", TRANSPARENT)
        self.win.configure(bg=WINDOW_BG)
        for attr in ("-toolwindow", "-disabled"):
            try: self.win.wm_attributes(attr, True)
            except tk.TclError: pass

        self.win.geometry(f"{EFX_W}x{EFX_H}+{wx}+{wy}")
        self.c = tk.Canvas(self.win, width=EFX_W, height=EFX_H,
                           bg=TRANSPARENT, highlightthickness=0)
        self.c.pack()

        # Sprite centre in canvas-local coordinates
        self.cx = sx + sw // 2 - wx
        self.cy = sy + sh // 2 - wy
        self._tick()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _burst(self, n, colors, spd=3, spread=math.pi, angle=None,
               life=20, size=4, grav=0.15):
        if angle is None:
            angle = 0 if self.facing == 1 else math.pi
        for _ in range(n):
            a = angle + random.uniform(-spread / 2, spread / 2)
            v = random.uniform(spd * 0.5, spd)
            self.parts.append(Particle(
                self.cx + random.randint(-4, 4),
                self.cy + random.randint(-4, 4),
                math.cos(a) * v, math.sin(a) * v,
                random.randint(life // 2, life),
                random.choice(colors),
                random.randint(2, size), grav,
            ))

    # ── Main tick ─────────────────────────────────────────────────────────────
    def _tick(self):
        try:
            if not self.win.winfo_exists():
                return
        except tk.TclError:
            return

        c, f = self.c, self.frame
        c.delete("all")
        cx, cy, facing = self.cx, self.cy, self.facing

        # ── Spawn logic ───────────────────────────────────────────────────────
        if self.fx == "razor_leaf" and f < 24 and f % 4 == 0:
            for _ in range(2):
                a = (0 if facing == 1 else math.pi) + random.uniform(-0.5, 0.5)
                s = random.uniform(5, 9)
                self.leaves.append(Particle(cx, cy, math.cos(a) * s, math.sin(a) * s,
                    30, random.choice(["#4CAF50","#66BB6A","#A5D6A7","#1B5E20"]),
                    8, grav=0.0))

        elif self.fx == "solar_beam" and f < 20:
            a    = random.uniform(0, 2 * math.pi)
            dist = random.uniform(55, 165)
            px, py = cx + math.cos(a) * dist, cy + math.sin(a) * dist
            self.parts.append(Particle(px, py, (cx - px) / 20, (cy - py) / 20,
                20, random.choice(["#FFD700","#FFF176","#FFEE58"]), 3, grav=0.0))

        elif self.fx == "sleep_powder" and f < 28 and f % 2 == 0:
            self._burst(2, ["#CE93D8","#BA68C8","#F48FB1","#80CBC4"],
                        spd=2.5, spread=math.pi * 1.6, angle=-math.pi / 2,
                        life=32, size=6, grav=0.02)

        elif self.fx == "ember" and f < 22:
            self._burst(3, ["#FF5722","#FF7043","#FFAB40","#FFD740"],
                        spd=4, spread=math.pi * 0.7, angle=-math.pi / 2,
                        life=18, size=5, grav=0.2)

        elif self.fx == "flamethrower" and f < 30:
            self._burst(5, ["#FF5722","#FF7043","#FF9800","#FFEB3B"],
                        spd=7, spread=0.35, life=15, size=7, grav=0.05)

        elif self.fx == "water_gun" and f < 26:
            self._burst(4, ["#1565C0","#1976D2","#42A5F5","#90CAF9"],
                        spd=7, spread=0.22, life=18, size=5, grav=0.3)

        elif self.fx == "bubble" and f % 6 == 0 and f < 32:
            for _ in range(2):
                self.bubbles.append([
                    float(cx + random.randint(-25, 25)), float(cy),
                    random.uniform(-1.6, -0.9),
                    random.randint(8, 15), 38, 38,
                ])

        elif self.fx == "bite" and f < 8:
            self._burst(6, ["#212121","#37474F","#78909C"],
                        spd=3, spread=math.pi * 2, life=12, size=4, grav=0.0)

        elif self.fx == "withdraw" and f % 5 == 0 and f < 22:
            for _ in range(3):
                a = random.uniform(0, 2 * math.pi)
                r = random.uniform(18, 40)
                self.parts.append(Particle(
                    cx + math.cos(a) * r, cy + math.sin(a) * r,
                    math.cos(a) * 0.4, math.sin(a) * 0.4,
                    22, random.choice(["#A5D6A7","#4CAF50","#1B5E20"]),
                    3, grav=0.0))

        # ── Update & draw circle particles ────────────────────────────────────
        alive = []
        for p in self.parts:
            p.step()
            if p.life > 0:
                p.draw(c); alive.append(p)
        self.parts = alive

        # ── Update & draw leaf particles ──────────────────────────────────────
        alive_l = []
        for p in self.leaves:
            p.step()
            if p.life > 0:
                a = math.atan2(p.vy, p.vx)
                pts = []
                for da, r in ((a, p.size * 2.8), (a + 2.4, p.size),
                              (a + math.pi, p.size * 2.8), (a - 2.4, p.size)):
                    pts += [p.x + math.cos(da) * r, p.y + math.sin(da) * r]
                c.create_polygon(pts, fill=p.color, outline="")
                alive_l.append(p)
        self.leaves = alive_l

        # ── Update & draw bubbles ─────────────────────────────────────────────
        alive_b = []
        for b in self.bubbles:
            bx, by, bvy, br, bl, bml = b
            by += bvy; bl -= 1
            if bl > 0:
                ar = max(2, int(br * bl / bml))
                c.create_oval(bx - ar, by - ar, bx + ar, by + ar,
                              outline="#42A5F5", width=2, fill="")
                alive_b.append([bx, by, bvy, br, bl, bml])
        self.bubbles = alive_b

        # ── Special vector drawings ───────────────────────────────────────────
        if self.fx == "vine_whip":
            ext = min(1.0, f / 12) * max(0.0, 1.0 - (f - 28) / 12)
            for sign in (1, -1):
                pts = [(cx, cy)]
                for seg in range(6):
                    prog = (seg + 1) / 6 * ext
                    x = cx + facing * prog * 200
                    y = (cy + sign * prog * 55
                         + math.sin(f * 0.4 + seg * 1.3) * 14 * prog)
                    pts.append((x, y))
                vcols = ["#1B5E20","#2E7D32","#388E3C","#43A047","#66BB6A","#A5D6A7"]
                for i in range(len(pts) - 1):
                    c.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1],
                                  fill=vcols[i], width=max(1, 5 - i),
                                  capstyle=tk.ROUND)

        elif self.fx == "solar_beam":
            if f >= 20:
                bp   = (f - 20) / 24
                blen = bp * 340
                bw   = max(5, int(7 + bp * 18))
                x2   = cx + facing * blen
                c.create_line(cx, cy, x2, cy, fill="#FDD835",
                              width=bw, capstyle=tk.ROUND)
                c.create_line(cx, cy, x2, cy, fill="#FFFDE7",
                              width=max(2, bw - 5), capstyle=tk.ROUND)
            else:
                r = 10 + f * 1.9
                c.create_oval(cx - r, cy - r, cx + r, cy + r,
                              outline="#FDD835", width=2)

        elif self.fx == "dragon_rage":
            for ring in range(3):
                t = (f - ring * 7) * 2.2
                if 0 < t < 80:
                    r   = t * 2.2
                    col = ["#AB47BC", "#7E57C2", "#E040FB"][ring]
                    c.create_oval(cx - r, cy - r, cx + r, cy + r,
                                  outline=col, width=3)

        elif self.fx == "scratch" and f < 16:
            slashes = [
                (cx - 8,  cy - 28, cx + 26, cy + 9),
                (cx,      cy - 22, cx + 34, cy + 15),
                (cx + 8,  cy - 16, cx + 42, cy + 21),
            ]
            for x1, y1, x2, y2 in slashes:
                if facing == -1:
                    x1 = cx - (x1 - cx); x2 = cx - (x2 - cx)
                c.create_line(x1, y1, x2, y2, fill="#FFFFFF",
                              width=3, capstyle=tk.ROUND)
                c.create_line(x1, y1, x2, y2, fill="#FFEE58",
                              width=1, capstyle=tk.ROUND)

        elif self.fx == "bite" and f < 15:
            gap = max(0, (15 - f) * 3)
            c.create_arc(cx - 32, cy - 32 - gap, cx + 32, cy - gap,
                         start=0,   extent=180, outline="#EF5350",
                         width=3, style=tk.ARC)
            c.create_arc(cx - 32, cy + gap, cx + 32, cy + 32 + gap,
                         start=180, extent=180, outline="#EF5350",
                         width=3, style=tk.ARC)

        elif self.fx == "withdraw" and f < 28:
            r = 22 + f * 0.65
            c.create_oval(cx - r, cy - r, cx + r, cy + r,
                          outline="#A5D6A7", width=2)
            if f < 20:
                c.create_line(cx - r * 0.7, cy, cx + r * 0.7, cy,
                              fill="#81C784", width=1)
                c.create_line(cx, cy - r * 0.7, cx, cy + r * 0.7,
                              fill="#81C784", width=1)

        self.frame += 1
        if self.frame < self.FRAMES:
            self.win.after(FRAME_MS, self._tick)
        else:
            try: self.win.destroy()
            except tk.TclError: pass


# ═══════════════════════════════════════════════════════════════════════════════
#  Professor Oak's Lab — Starter selection
# ═══════════════════════════════════════════════════════════════════════════════
class StarterSelect:
    """Carousel selection screen: left/right arrows flip through
    the starters inside a big viewfinder card; Choose (or Enter)
    confirms.  Keyboard: Left / Right / Return."""

    W, H    = 560, 560
    CARD    = (120, 96, 440, 440)     # the viewfinder frame
    SHOTSCALE = 3                     # sprite scale inside the frame

    def __init__(self, root, cache: dict, lines: list, callback,
                 quit_on_close=True):
        self.root     = root
        self.cache    = cache      # {(pid, shiny): (rights, lefts, w, h)}
        self.lines    = lines
        # key out the magenta sprite background and composite over
        # the viewfinder colour, at the big display scale
        keyed = {}
        for (pid, shiny), v in self.cache.items():
            path = sprite_path(pid, shiny)
            if os.path.exists(path):
                keyed[(pid, shiny)] = load_frames(
                    path, scale=self.SHOTSCALE, keyout_bg="#162412")
        if keyed:
            self.cache = keyed
        self.callback = callback   # callback(line_idx: int)
        self.quit_on_close = quit_on_close
        self.hover    = None
        self.frame    = 0
        self.done     = False
        self.sel      = 0

        # Static background stars / foliage dots
        self.stars = [
            (random.randint(0, self.W), random.randint(0, 560),
             random.choice(["#2D4E1F", "#3A6A2A", "#1E3A14", "#4A7A30"]))
            for _ in range(60)
        ]

        self.win = tk.Toplevel(root)
        self.win.title("EeveeMon — Choose your starter!")
        self.win.resizable(True, True)
        self.win.minsize(400, 400)
        self.win.protocol("WM_DELETE_WINDOW", self._quit)

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(
            f"{self.W}x{self.H}"
            f"+{(sw - self.W) // 2}+{(sh - self.H) // 2}"
        )

        self.c = tk.Canvas(self.win, width=self.W, height=self.H,
                           bg="#0E1F09", highlightthickness=0)
        self.c.pack(fill="both", expand=True)
        self._scl, self._ox, self._oy = 1.0, 0, 0
        self.c.bind("<Motion>",   self._on_motion)
        self.c.bind("<Button-1>", self._on_click)
        self.win.bind("<Left>",  lambda e: self._flip(-1))
        self.win.bind("<Right>", lambda e: self._flip(1))
        self.win.bind("<Return>", lambda e: self._choose())

        self._tick()

        # EEM_SHOT env hook: export the screen and exit
        if os.environ.get("EEM_SHOT"):
            self.win.update_idletasks()
            def _shot():
                from PIL import ImageGrab
                self.win.lift()
                self.win.attributes("-topmost", True)
                self.c.update_idletasks()
                c = self.c
                x, y = c.winfo_rootx(), c.winfo_rooty()
                w, h = c.winfo_width(), c.winfo_height()
                full = ImageGrab.grab()
                scale = full.width / self.win.winfo_screenwidth()
                full.crop((int(x * scale), int(y * scale),
                           int((x + w) * scale),
                           int((y + h) * scale))).save(
                    os.environ["EEM_SHOT"])
                self.win.destroy()
            if os.environ.get("EEM_SHOT_W"):
                self.win.geometry(os.environ["EEM_SHOT_W"])
            self.win.after(6000, _shot)

    # ── Events ────────────────────────────────────────────────────────────────
    def _quit(self):
        if self.quit_on_close:
            sys.exit(0)
        self.done = True
        self.win.destroy()

    def _hit(self, e):
        scl = getattr(self, "_scl", 1.0) or 1.0
        ox = getattr(self, "_ox", 0)
        oy = getattr(self, "_oy", 0)
        x = (e.x - ox) / scl
        y = (e.y - oy) / scl
        if 24 <= x <= 96 and 220 <= y <= 360:
            return "left"
        if self.W - 96 <= x <= self.W - 24 and 220 <= y <= 360:
            return "right"
        if self.W // 2 - 90 <= x <= self.W // 2 + 90 \
                and 496 <= y <= 548:
            return "choose"
        return None

    def _on_motion(self, e):
        self.hover = self._hit(e)

    def _on_click(self, e):
        if self.done:
            return
        z = self._hit(e)
        if z == "left":
            self._flip(-1)
        elif z == "right":
            self._flip(1)
        elif z == "choose":
            self._choose()

    def _flip(self, d):
        self.sel = (self.sel + d) % min(len(self.lines), 8)
        self.frame = 0

    def _choose(self):
        if self.done:
            return
        self.done = True
        self._flash(self.sel)

    def _flash(self, idx: int):
        self.c.create_rectangle(0, 0, self.W, self.H, fill="#FFFFFF",
                                outline="")
        self.win.update()
        self.win.after(110, lambda: self._finish(idx))

    def _finish(self, idx: int):
        self.callback(idx)
        self.win.destroy()

    # ── Colour helper ─────────────────────────────────────────────────────────
    @staticmethod
    def _dim(hexcol: str, f: float):
        h = hexcol.lstrip("#")
        return "#" + "".join(f"{max(0, int(int(h[i:i+2], 16) * f)):02x}"
                             for i in (0, 2, 4))

    def _tick(self):
        if self.done or not self.win.winfo_exists():
            return

        c, f = self.c, self.frame
        c.delete("all")

        # Background
        c.create_rectangle(0, 0, self.W, self.H, fill="#0E1F09",
                           outline="")
        for sx, sy, sc in self.stars:
            c.create_oval(sx - 1, sy - 1, sx + 1, sy + 1, fill=sc,
                          outline="")

        # Title
        c.create_text(self.W // 2, 34,
                      text="Choose your starter, trainer!",
                      fill="#A8C898", font=("Segoe UI", 12, "italic"))

        line = self.lines[self.sel]
        col = line["color"]
        evo0 = line["evolutions"][0]
        x0, y0, x1, y1 = self.CARD
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2

        # the viewfinder frame
        if self.hover == "choose":
            pass
        c.create_rectangle(x0, y0, x1, y1, fill="#162412", outline="")
        c.create_rectangle(x0, y0, x1, y1, fill="", outline=col,
                           width=4)
        # inner corners (camera viewfinder marks)
        for (mx, my) in ((x0 + 14, y0 + 14), (x1 - 14, y0 + 14),
                         (x0 + 14, y1 - 14), (x1 - 14, y1 - 14)):
            c.create_rectangle(mx - 4, my - 4, mx + 4, my + 4,
                               fill=col, outline="")

        # the sprite with bob
        pid = evo0["id"]
        if (pid, False) in self.cache:
            frames_r, _, sw_, sh_ = self.cache[(pid, False)]
            fidx = f % len(frames_r)
            bob = int(math.sin(f * 0.12) * 6)
            c.create_image(cx - sw_ // 2, cy - sh_ // 2 + bob - 20,
                           anchor="nw", image=frames_r[fidx])

        # name + type + page indicator
        c.create_text(cx, y1 - 44, text=evo0["name"], fill="#FFFFFF",
                      font=("Segoe UI", 16, "bold"))
        c.create_text(cx, y1 - 22, text=line["type"], fill=col,
                      font=("Segoe UI", 10))
        dots = "●" * self.sel + "○" * (min(len(self.lines), 8)
                                       - self.sel - 1)
        c.create_text(cx, y0 + 20, text=dots, fill="#4A6840",
                      font=("Segoe UI", 11))

        # left / right arrows
        for tag, tri, hov in (("left", (40, 290, 88, 250, 88, 330),
                               self.hover == "left"),
                              ("right", (self.W - 40, 290,
                                         self.W - 88, 250,
                                         self.W - 88, 330),
                               self.hover == "right")):
            c.create_polygon(*tri,
                             fill="#C9A227" if hov else "#6B5A2E",
                             outline="#F5C518" if hov else "#4A3F1E",
                             width=2)

        # Choose button
        bx0, bx1 = self.W // 2 - 90, self.W // 2 + 90
        by0, by1 = 496, 548
        hov = (self.hover == "choose")
        c.create_rectangle(bx0, by0, bx1, by1,
                           fill="#C9A227" if hov else "#6B5A2E",
                           outline="#F5C518", width=2)
        c.create_text(self.W // 2, (by0 + by1) // 2,
                      text="Choose!", fill="#FFFFFF",
                      font=("Segoe UI", 13, "bold"))

        # ── Free-resize: scale the whole scene to the window ──
        cw = max(1, c.winfo_width())
        ch = max(1, c.winfo_height())
        scl = max(min(cw / self.W, ch / self.H), 0.5)
        if abs(scl - 1.0) > 0.001:
            c.scale("all", 0, 0, scl, scl)
        ox = (cw - self.W * scl) / 2
        oy = (ch - self.H * scl) / 2
        if ox or oy:
            c.move("all", ox, oy)
        self._scl, self._ox, self._oy = scl, ox, oy
        bg = c.create_rectangle(0, 0, cw, ch, fill="#0E1F09",
                                outline="")
        c.tag_lower(bg)

        self.frame += 1
        self.win.after(FRAME_MS, self._tick)



class ChatBubble:
    """Speech bubble in the Pokemon-game style: the box appears
    pre-sized to the final message, the text types out character
    by character, and the whole bubble follows the sprite as it
    walks (tail tracks the sprite's centre x)."""
    PAD       = 14
    TAIL      = 14
    LIFE      = 9000    # ms before auto-dismiss
    CHAR_MS   = 26      # typewriter cadence per character
    PUNCT_MS  = 240     # pause after sentence punctuation
    FOLLOW_MS = 120     # position-refresh cadence

    def __init__(self, root, buddy, name, col, text):
        self.root  = root
        self.buddy = buddy
        self.full_text = textwrap.fill(text, width=34)
        # the auto-dismiss waits for the typewriter to finish:
        # long replies were being cut mid-sentence
        self.LIFE = max(9000, 6000 + len(self.full_text)
                        * self.CHAR_MS)

        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        if MAC:
            try: self.win.wm_attributes("-transparent", True)
            except tk.TclError: pass
        else:
            self.win.attributes("-transparentcolor", TRANSPARENT)
        self.win.configure(bg=WINDOW_BG)
        # -disabled = CLICK-THROUGH: right-clicks pass through
        # the bubble to the sprite beneath (the bubble blocked
        # the menu) -- also stops the bubble stealing focus
        for attr in ("-toolwindow", "-disabled"):
            try: self.win.wm_attributes(attr, True)
            except tk.TclError: pass
        self._last_geom = None
        self._lift_n = 0

        # pre-size the bubble to the FINAL text: measure the
        # wrapped text's natural width and height, then adapt the
        # bubble to it (the game-dialog feel: box first, text
        # types into it)
        _m = tk.Label(self.win, text=self.full_text,
                      font=("Segoe UI", 10), wraplength=340,
                      justify="left")
        _m.pack(); self.win.update_idletasks()
        th = _m.winfo_reqheight()
        tw = _m.winfo_reqwidth()
        _m.destroy()

        name_h   = 20
        self.W   = max(120, min(360, tw + 2 * self.PAD))
        body_h   = self.PAD + name_h + 6 + th + self.PAD
        self.total_h = body_h + self.TAIL

        # bubble above the sprite; below when the sprite sits
        # near the screen top (chosen once, stable for this bubble)
        self.above = (int(buddy.y) - self.total_h - 6) > 8
        self.c = tk.Canvas(self.win, width=self.W,
                           height=self.total_h,
                           bg=WINDOW_BG, highlightthickness=0)
        self.c.pack()
        self._draw_shape(name, col, body_h, name_h)
        self._reposition()

        self.win.bind("<Button-1>", lambda e: self._dismiss())
        self.win.deiconify()
        self._ti = 0
        self._type()
        self._follow()
        self.win.after(self.LIFE, self._dismiss)

    def _draw_shape(self, name, col, body_h, name_h):
        tx = self.W // 2
        if self.above:
            self.c.create_rectangle(0, 0, self.W, body_h,
                                    fill=col, outline="")
            self.c.create_rectangle(2, 2, self.W - 2, body_h - 2,
                                    fill="#1E1E20", outline="")
            self.tail_item = self.c.create_polygon(
                tx - 10, body_h, tx + 10, body_h, tx, self.total_h,
                fill=col, outline="")
            text_y0 = self.PAD
        else:
            self.tail_item = self.c.create_polygon(
                tx - 10, 0, tx + 10, 0, tx, self.TAIL,
                fill=col, outline="")
            self.c.create_rectangle(0, self.TAIL, self.W,
                                    self.total_h, fill=col,
                                    outline="")
            self.c.create_rectangle(2, self.TAIL + 2, self.W - 2,
                                    self.total_h - 2,
                                    fill="#1E1E20", outline="")
            text_y0 = self.TAIL + self.PAD

        self.c.create_text(self.PAD, text_y0, text=name, fill=col,
                           font=("Segoe UI", 9, "bold"),
                           anchor="nw")
        self.c.create_line(self.PAD, text_y0 + name_h + 1,
                           self.W - self.PAD,
                           text_y0 + name_h + 1, fill=col, width=1)
        # the message: starts empty, fills in via the typewriter
        self.msg_item = self.c.create_text(
            self.PAD, text_y0 + name_h + 8, text="",
            fill="#F0F0F0", font=("Segoe UI", 10), anchor="nw",
            width=self.W - self.PAD * 2, justify=tk.LEFT)

    def _type(self):
        if getattr(self, "_dead", False):
            return
        n = self._ti
        if n < len(self.full_text):
            ch = self.full_text[n]
            self._ti = n + 1
            self.c.itemconfigure(self.msg_item,
                                 text=self.full_text[:n + 1])
            delay = self.PUNCT_MS if ch in ".!?。" else self.CHAR_MS
            self.win.after(delay, self._type)

    def _follow(self):
        if getattr(self, "_dead", False):
            return
        try:
            self._reposition()
            self.win.after(self.FOLLOW_MS, self._follow)
        except tk.TclError:
            pass

    def _reposition(self):
        b  = self.buddy
        sx, sy = int(b.x), int(b.y)
        sw, sh = int(b.sw), int(b.sh)
        scr_w = self.root.winfo_screenwidth()
        bx = max(8, min(sx + sw // 2 - self.W // 2,
                        scr_w - self.W - 8))
        by = ((sy - self.total_h - 6)
              if self.above else (sy + sh + 6))
        # only touch geometry when it actually CHANGES -- the
        # constant geometry()+lift() every 120ms was the flicker
        geom = (bx, by)
        if geom != self._last_geom:
            self._last_geom = geom
            self.win.geometry(f"{self.W}x{self.total_h}+{bx}+{by}")
            try:
                self.win.attributes("-topmost", True)
                self.win.lift()
            except tk.TclError:
                pass
        # the tail tracks the sprite's centre x inside the bubble
        tx = max(12, min(self.W - 12, sx + sw // 2 - bx))
        if self.above:
            self.c.coords(self.tail_item, tx - 10, self.total_h - self.TAIL,
                          tx + 10, self.total_h - self.TAIL,
                          tx, self.total_h)
        else:
            self.c.coords(self.tail_item, tx - 10, 0, tx + 10, 0,
                          tx, self.TAIL)

    def _dismiss(self):
        self._dead = True
        try: self.win.destroy()
        except tk.TclError: pass


class AgentMind:
    """Gives the Pokémon buddy a personality and screen awareness via Claude."""

    MODEL = "claude-haiku-4-5-20251001"

    def __init__(self, buddy):
        self.buddy   = buddy
        self._client = None
        # short conversation memory: the last few exchanges are
        # replayed so the pet actually remembers what you said
        self.history = []   # [(role, text), ...]
        # thread-safe inbox: worker threads never touch Tk
        # directly; the main loop drains this queue instead
        self._inbox = queue.Queue()
        self.buddy.root.after(250, self._drain)
        self._setup()

    def _app_dir(self) -> str:
        # next to the exe when frozen, else the script dir
        if getattr(sys, "frozen", False):
            return os.path.dirname(os.path.abspath(sys.executable))
        return os.path.dirname(os.path.abspath(__file__))

    def _load_config(self):
        """provider.txt: line 1 = provider (deepseek/openai/
        anthropic, default deepseek), line 2 = model (optional).
        Key from apikey.txt / deepseek_key.txt next to the app;
        when frozen, the PARENT folder (the one the user unzipped)
        is searched too -- dist\\EeveeMon.exe sees the key files
        placed next to the exe OR next to the dist folder."""
        dirs = [self._app_dir()]
        if getattr(sys, "frozen", False):
            parent = os.path.dirname(self._app_dir())
            if parent != self._app_dir():
                dirs.append(parent)
        provider, model = "deepseek", ""
        for d in dirs:
            pf = os.path.join(d, "provider.txt")
            if os.path.exists(pf):
                lines = [l.strip() for l in
                         open(pf, encoding="utf-8")
                         .read().splitlines()]
                if lines and lines[0]:
                    provider = lines[0].lower()
                if len(lines) > 1 and lines[1]:
                    model = lines[1]
                break
        key = ""
        for d in dirs:
            for kf in ("apikey.txt", "deepseek_key.txt"):
                fp = os.path.join(d, kf)
                if os.path.exists(fp):
                    key = open(fp, encoding="utf-8").read().strip()
                    break
            if key:
                break
        return provider, model, key

    def _setup(self):
        provider, model, key = self._load_config()
        if not key:
            key = self._ask_key()
        if key:
            self._client = key
            self._provider = provider
            self._model = model
            self._schedule_passive()

    def _ask_key(self) -> str:
        """Show a simple dialog asking for the API key."""
        result = [""]
        dlg = tk.Toplevel(self.buddy.root)
        dlg.title("BuddyMon — AI Companion")
        dlg.resizable(False, False)
        dlg.configure(bg="#1C1C1E")
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        dlg.geometry(f"420x175+{(sw-420)//2}+{(sh-175)//2}")

        tk.Label(dlg, text="Enter your API key (DeepSeek / OpenAI / Anthropic)\nthe Pokémon AI companion:",
                 bg="#1C1C1E", fg="#FFFFFF",
                 font=("Segoe UI", 11)).pack(pady=(18, 8))

        entry = tk.Entry(dlg, width=46, show="*", font=("Consolas", 10),
                         bg="#2C2C2E", fg="#FFFFFF", insertbackground="#FFFFFF",
                         relief="flat")
        entry.pack(padx=20, ipady=4)

        f = tk.Frame(dlg, bg="#1C1C1E")
        f.pack(pady=14)

        def confirm():
            result[0] = entry.get().strip(); dlg.destroy()

        tk.Button(f, text="Confirm", command=confirm,
                  bg="#4CAF50", fg="#FFFFFF", font=("Segoe UI", 10),
                  relief="flat", padx=12).pack(side="left", padx=6)
        tk.Button(f, text="Skip (AI disabled)", command=dlg.destroy,
                  bg="#636366", fg="#FFFFFF", font=("Segoe UI", 10),
                  relief="flat", padx=12).pack(side="left")

        entry.bind("<Return>", lambda e: confirm())
        dlg.grab_set()
        dlg.wait_window()
        return result[0]

    # ── Personality ───────────────────────────────────────────────────────────
    def _system(self) -> str:
        evo    = STARTER_LINES[self.buddy.line_idx]["evolutions"][self.buddy.evo_stage]
        name   = evo["name"]
        shiny  = "  You are a rare shiny variant — this makes you feel extra special." if self.buddy.is_shiny else ""
        base   = PERSONALITIES.get(name, f"You are {name}, a Pokémon desktop buddy.")
        return f"{base}{shiny}  Keep every response to 1–3 short sentences. Stay in character at all times."

    # ── Public triggers ───────────────────────────────────────────────────────
    def greet(self):
        evo = STARTER_LINES[self.buddy.line_idx]["evolutions"][self.buddy.evo_stage]
        self._call(f"Greet your trainer for the very first time! You just arrived on their desktop as a buddy. Introduce yourself as {evo['name']}.")

    def speak(self, prompt: str = ""):
        if not prompt:
            prompt = random.choice([
                "Say something fun and in-character. You're a desktop buddy just hanging out.",
                "Comment on being on a computer all day, in character.",
                "Express how you feel right now, briefly.",
                "Say something encouraging to your trainer.",
                "React to sitting on the taskbar all day in character.",
            ])
        self._call(prompt)

    def look_around(self):
        """Capture the screen and have the Pokémon comment on it."""
        if not self._client:
            return
        threading.Thread(target=self._look_thread, daemon=True).start()

    def on_evolve(self):
        evo = STARTER_LINES[self.buddy.line_idx]["evolutions"][self.buddy.evo_stage]
        self._call(f"You just evolved into {evo['name']}! React with excitement, surprise, or whatever fits your personality.")

    # ── Internals ─────────────────────────────────────────────────────────────
    def _call(self, prompt: str):
        if not self._client:
            return
        threading.Thread(target=self._api_thread, args=(prompt,), daemon=True).start()

    def _api_thread(self, prompt: str):
        try:
            provider = getattr(self, "_provider", "deepseek")
            model = getattr(self, "_model", "") or {
                "deepseek": "deepseek-chat",
                "openai": "gpt-4o-mini",
                "anthropic": "claude-3-5-haiku-latest",
            }.get(provider, "deepseek-chat")
            sysmsg = self._system()
            if provider == "anthropic":
                payload = json.dumps({
                    "model": model,
                    "max_tokens": 120,
                    "system": sysmsg,
                    "messages": [{"role": r, "content": t}
                                 for (r, t) in self.history[-6:]] + [
                        {"role": "user", "content": prompt}],
                }).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=payload,
                    headers={"Content-Type": "application/json",
                             "x-api-key": self._client,
                             "anthropic-version": "2023-06-01"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = json.loads(r.read().decode("utf-8"))
                text = body["content"][0]["text"].strip()
            else:
                url = ("https://api.openai.com/v1/chat/completions"
                       if provider == "openai" else
                       "https://api.deepseek.com/chat/completions")
                payload = json.dumps({
                    "model": model,
                    "max_tokens": 120,
                    "messages": [
                        {"role": "system", "content": sysmsg},
                    ] + [{"role": r, "content": t}
                         for (r, t) in self.history[-6:]] + [
                        {"role": "user", "content": prompt},
                    ],
                }).encode("utf-8")
                req = urllib.request.Request(
                    url, data=payload,
                    headers={"Content-Type": "application/json",
                             "Authorization":
                             f"Bearer {self._client}"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = json.loads(r.read().decode("utf-8"))
                text = body["choices"][0]["message"][
                    "content"].strip()
            self.history.append(("user", prompt))
            self.history.append(("assistant", text))
            self.history = self.history[-6:]
            self._inbox.put(("say", text))
        except Exception as exc:
            self._inbox.put(("err", str(exc)[:80]))
            print(f"[AgentMind] {exc}", flush=True)
            # the full error + response body land in a log next
            # to the app (chat failures are otherwise opaque)
            try:
                import datetime as _dt
                with open(os.path.join(self._app_dir(),
                                       "eeveemon_chat.log"),
                          "a", encoding="utf-8") as lf:
                    lf.write(f"[{_dt.datetime.now():%Y-%m-%d %H:%M:%S}] "
                             f"{provider} {model}: "
                             f"{type(exc).__name__}: {exc}\n")
                    if isinstance(exc, urllib.error.HTTPError):
                        lf.write("  body: "
                                 + exc.read().decode("utf-8",
                                                     "replace")[:400]
                                 + "\n")
            except OSError:
                pass

    def _look_thread(self):
        try:
            from PIL import ImageGrab
            shot = ImageGrab.grab()
            shot = shot.resize((1024, 576), Image.LANCZOS)
            buf  = io.BytesIO()
            shot.save(buf, format="PNG")
            img_b64 = base64.standard_b64encode(buf.getvalue()).decode()

            provider = getattr(self, "_provider", "deepseek")
            model = getattr(self, "_model", "") or {
                "deepseek": "deepseek-chat",
                "openai": "gpt-4o-mini",
                "anthropic": "claude-3-5-haiku-latest",
            }.get(provider, "deepseek-chat")
            sysmsg = self._system()
            prompt = ("Look at this screenshot of the user's "
                      "screen. Comment in-character as your "
                      "Pokémon persona, under 2 sentences.")
            if provider == "openai":
                # gpt-4o-mini is vision-capable: real screen
                # comment via the image_url payload
                payload = json.dumps({
                    "model": model,
                    "max_tokens": 300,
                    "messages": [
                        {"role": "system", "content": sysmsg},
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {
                                "url": "data:image/png;base64,"
                                + img_b64}}]}],
                }).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.openai.com/v1/chat/completions",
                    data=payload,
                    headers={"Content-Type": "application/json",
                             "Authorization": "Bearer "
                             + self._client})
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = json.loads(r.read().decode("utf-8"))
                text = body["choices"][0]["message"]["content"].strip()
                self._inbox.put(("say", text))
                return
            if provider == "anthropic":
                # claude haiku is vision-capable: base64 image
                # block in the messages content
                payload = json.dumps({
                    "model": model,
                    "max_tokens": 300,
                    "system": sysmsg,
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_b64}}]}],
                }).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=payload,
                    headers={"Content-Type": "application/json",
                             "x-api-key": self._client,
                             "anthropic-version": "2023-06-01"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = json.loads(r.read().decode("utf-8"))
                text = body["content"][0]["text"].strip()
                self._inbox.put(("say", text))
                return
            # deepseek: v4-pro ignores images BUT deepseek-flash
            # accepts the standard OpenAI-style image payload
            # (tested 2026-09-17: it answered 'Red' on a base64
            # test image) -- use flash for the look
            payload = json.dumps({
                "model": "deepseek-flash",
                "max_tokens": 300,
                "messages": [
                    {"role": "system", "content": sysmsg},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": "data:image/png;base64,"
                            + img_b64}}]}],
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.deepseek.com/chat/completions",
                data=payload,
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer "
                         + self._client})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = json.loads(r.read().decode("utf-8"))
            text = body["choices"][0]["message"]["content"].strip()
            if text:
                self._inbox.put(("say", text))
            else:
                self._inbox.put(("say",
                    "（偷偷看了一眼你的屏幕，只看到一堆发光的方块。）"))
        except Exception as exc:
            self._inbox.put(("err", f"Look Around 失败：{exc}"))

    def _drain(self):
        try:
            while True:
                kind, text = self._inbox.get_nowait()
                if kind == "err":
                    text = f"（AI 服务连接失败：{text}）"
                self._show(text)
        except queue.Empty:
            pass
        try:
            self.buddy.root.after(250, self._drain)
        except tk.TclError:
            pass

    def _show(self, text: str):
        # dismiss the previous bubble first -- stacked bubbles
        # were a flicker/overlap source
        prev = getattr(self, "_bubble", None)
        if prev is not None:
            try:
                prev._dismiss()
            except Exception:
                pass
        line = STARTER_LINES[self.buddy.line_idx]
        evo  = line["evolutions"][self.buddy.evo_stage]
        self._bubble = ChatBubble(self.buddy.root, self.buddy,
                                  evo["name"], line["color"], text)

    def _schedule_passive(self):
        # First comment 3–6 min after start, then every 8–15 min
        delay = random.randint(3 * 60_000, 6 * 60_000)
        self.buddy.root.after(delay, self._passive)

    def _passive(self):
        self.speak()
        self._schedule_passive()


# ═══════════════════════════════════════════════════════════════════════════════
#  Buddy — the taskbar sprite
# ═══════════════════════════════════════════════════════════════════════════════
class Buddy:
    """Main desktop buddy: walks on the taskbar, responds to right-click."""

    def __init__(self):
        self.line_idx  = 0
        self.evo_stage = 0
        self.is_shiny  = False
        self.size_pct  = 100   # 100 = default (SCALE×2)
        self.agent     = None  # set after selection screen
        # the collection book: every form ever chosen/evolved
        # into this session {(line_idx, stage), ...}.  Starts
        # EMPTY -- choosing a starter unlocks its first card
        # (the restore path below fills it from the save file)
        self.unlocked  = set()
        self._album_imgs = []
        # evolution-stone inventory (the light item system)
        self.inventory = {"水之石": 1, "雷之石": 1, "火之石": 1,
                          "叶之石": 1, "冰之石": 1}
        self._gift_until = 0.0   # Gift cooldown deadline
        # restore a saved pet if one exists (the collection book
        # and stone economy persist across restarts)
        self._started = False
        save = self._load_state()
        if save:
            try:
                self.line_idx = int(save["line_idx"])
                self.evo_stage = int(save["evo_stage"])
                self.is_shiny = bool(save.get("is_shiny", False))
                self.size_pct = int(save.get("size_pct", 100))
                self.inventory.update(save.get("inventory", {}))
                self.unlocked = {tuple(k) for k in
                                 save.get("unlocked", [])}
                if not self.unlocked:
                    self.unlocked = {(self.line_idx,
                                      self.evo_stage)}
                self._gift_until = float(save.get("gift_until",
                                                 0.0))
                self._started = True
            except (KeyError, ValueError, TypeError):
                pass

        # Download sprites (skipped if already cached)
        print("EeveeMon — Checking sprites...", flush=True)
        for pid in ALL_IDS:
            ensure_sprite(pid, shiny=False)
            ensure_sprite(pid, shiny=True)
        print("All sprites ready.\n", flush=True)

        # Hidden root window (becomes the buddy after selection)
        self.root = tk.Tk()
        self.root.withdraw()

        self.scr_w = self.root.winfo_screenwidth()
        self.scr_h = self.root.winfo_screenheight()

        # Load ONLY the starter sprites at default scale (the
        # Tk pixmap budget can't hold all 48 GIFs at once --
        # the rest load lazily in _apply/_change_line)
        self._cache: dict = {}
        starters = [line["evolutions"][0]["id"]
                    for line in STARTER_LINES]
        for pid in starters:
            for shiny in (False, True):
                p = sprite_path(pid, shiny)
                if os.path.exists(p):
                    self._cache[(pid, shiny, SCALE)] = load_frames(
                        p, scale=SCALE)

        # Build a default-scale view for the selection screen
        _select_cache = {(pid, shiny): v
                         for (pid, shiny, sc), v in self._cache.items()
                         if sc == SCALE}

        if not self._started:
            # Show starter selection
            select = StarterSelect(self.root, _select_cache,
                                   STARTER_LINES, self._on_chosen)
            self.root.wait_window(select.win)

            if not getattr(self, "_started", False):
                return  # window closed without choosing

        # ── Configure root as the buddy window ────────────────────────────────
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        if MAC:
            try: self.root.wm_attributes("-transparent", True)
            except tk.TclError: pass
        else:
            self.root.attributes("-transparentcolor", TRANSPARENT)
        self.root.configure(bg=WINDOW_BG)
        try: self.root.wm_attributes("-toolwindow", True)
        except tk.TclError: pass
        self.root.deiconify()

        self._apply()

        self.x         = float(random.randint(50, max(51, self.scr_w - self.sw - 50)))
        self.y         = float(-self.sh)
        self.root.geometry(f"{self.sw}x{self.sh}+{int(self.x)}+{int(self.y)}")

        self.vy        = 0.0
        self.state     = "falling"
        self.facing    = 1
        self.frame_i   = 0
        self.action_cd = 0

        self._drag_ox = self._drag_oy = 0
        self._click_x0 = self._click_y0 = 0
        self._dragging = False

        self.canvas.bind("<ButtonPress-1>",   self._press)
        self.canvas.bind("<B1-Motion>",       self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Button-3>",        self._show_menu)

        self._build_menu()

        # Start AI companion (prompts for API key if needed)
        self.agent = AgentMind(self)
        self._build_menu()   # rebuild: Talk/Look enable when the
                             # agent has a key
        self.root.after(4000, self.agent.greet)  # greet after landing

        self._tick()
        self.root.mainloop()

    # ── Save / load (the collection book persists) ────────────────────────────
    def _save_state(self):
        try:
            data = {
                "line_idx": self.line_idx,
                "evo_stage": self.evo_stage,
                "is_shiny": self.is_shiny,
                "size_pct": self.size_pct,
                "inventory": self.inventory,
                "unlocked": sorted([list(k) for k in
                                    getattr(self, "unlocked", set())]),
                "gift_until": self._gift_until,
            }
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except OSError:
            pass

    def _load_state(self):
        if not os.path.exists(SAVE_PATH):
            return None
        try:
            with open(SAVE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    # ── Starter selection callback ────────────────────────────────────────────
    def _on_chosen(self, line_idx: int):
        self.line_idx  = line_idx
        self.evo_stage = 0
        if getattr(self, "unlocked", None) is not None:
            self.unlocked.add((line_idx, 0))
        self.is_shiny  = random.random() < (1 / SHINY_CHANCE)
        self._started  = True
        self._save_state()

    # ── Sprite management ─────────────────────────────────────────────────────
    def _apply(self):
        """Apply current line/stage/shiny/size to the sprite."""
        evo   = STARTER_LINES[self.line_idx]["evolutions"][self.evo_stage]
        pid   = evo["id"]
        scale = round(self.size_pct / 100 * SCALE, 4)
        key   = (pid, self.is_shiny, scale)

        if (pid, self.is_shiny, SCALE) not in self._cache:
            self.is_shiny = False   # fallback if shiny sprite missing

        if key not in self._cache:
            p = sprite_path(pid, self.is_shiny)
            if os.path.exists(p):
                self._cache[key] = load_frames(p, scale=scale)
            else:
                key = (pid, self.is_shiny, SCALE)  # fallback to default size

        r, l, w, h = self._cache[key]
        self.frames_r, self.frames_l = r, l
        self.sw, self.sh = w, h
        self.ground_y = float(self.scr_h - TASKBAR_H - self.sh)
        self.n_frames  = len(r)

        if hasattr(self, "canvas"):
            self.canvas.config(width=self.sw, height=self.sh)
        else:
            self.canvas = tk.Canvas(
                self.root, width=self.sw, height=self.sh,
                bg=TRANSPARENT, highlightthickness=0,
            )
            self.canvas.pack()

        self.root.geometry(
            f"{self.sw}x{self.sh}"
            f"+{int(getattr(self,'x',0))}+{int(getattr(self,'y',0))}"
        )

    # ── Evolution ─────────────────────────────────────────────────────────────
    EEVEE_LINE = 3   # the Eevee line index in STARTER_LINES

    def _evo_available(self, evo) -> bool:
        req = evo.get("req", "")
        if not req or req == "friend":
            return True
        if req.startswith("stone:"):
            return self.inventory.get(req.split(":", 1)[1], 0) > 0
        return True

    def _evo_label(self, evo) -> str:
        lbl = evo["name"]
        if evo.get("method"):
            lbl += f"  ({evo['method']})"
        req = evo.get("req", "")
        if req.startswith("stone:"):
            stone = req.split(":", 1)[1]
            n = self.inventory.get(stone, 0)
            lbl += f"  ×{n}"
            if n == 0:
                lbl += "  [已用尽]"
        return lbl

    def _evolve_to(self, stage: int):
        evo = STARTER_LINES[self.line_idx]["evolutions"][stage]
        if not self._evo_available(evo):
            return
        req = evo.get("req", "")
        if req.startswith("stone:"):
            self.inventory[req.split(":", 1)[1]] -= 1
        self.evo_stage = stage
        if getattr(self, "unlocked", None) is not None:
            self.unlocked.add((self.line_idx, stage))
        self.frame_i = 0
        self._save_state()
        self._apply()
        self._evo_flash()
        self._build_menu()
        self.root.after(500, self.agent.on_evolve)

    def _gift(self):
        """A random evolution stone; 10-minute cooldown keeps the
        stone economy honest."""
        if time.time() < self._gift_until:
            return
        stone = random.choice(list(self.inventory.keys()))
        self.inventory[stone] += 1
        self._gift_until = time.time() + 600
        self._save_state()
        self._build_menu()

    def _evolve(self):
        line = STARTER_LINES[self.line_idx]
        n = len(line["evolutions"])
        if self.line_idx == self.EEVEE_LINE:
            # branching: Eevee -> any of the 8 Eeveelutions
            m = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 9))
            m.add_command(label="Evolve into...", state="disabled")
            m.add_separator()
            for i, evo in enumerate(line["evolutions"][1:], start=1):
                m.add_command(label=self._evo_label(evo),
                              state="normal" if self._evo_available(evo)
                              else "disabled",
                              command=lambda s=i: self._evolve_to(s))
            m.tk_popup(self.x + self.sw // 2, self.y + self.sh // 2)
        elif self.evo_stage < n - 1:
            self._evolve_to(self.evo_stage + 1)

    def _devolve(self):
        if self.line_idx == self.EEVEE_LINE and self.evo_stage > 0:
            # Eeveelutions devolve straight back to Eevee
            self.evo_stage = 0
            self.frame_i = 0
            self._save_state()
            self._apply()
            self._evo_flash()
            self._build_menu()
            return
        if self.evo_stage > 0:
            self.evo_stage -= 1
            self.frame_i = 0
            self._save_state()
            self._apply()
            self._build_menu()

    def _evo_flash(self):
        """Pokemon-games-style white flash on evolution."""
        w = tk.Toplevel(self.root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        try: w.wm_attributes("-toolwindow", True)
        except tk.TclError: pass
        w.geometry(f"{self.sw}x{self.sh}+{int(self.x)}+{int(self.y)}")
        w.configure(bg="#FFFFFF")
        w.after(120, w.destroy)

    # ── Starter line change ────────────────────────────────────────────────────
    def _open_select(self):
        """Re-open the animated selection screen (menu option)."""
        # reduce to (pid, shiny) keys -- the StarterSelect cache
        # format (mirrors the startup _select_cache build)
        select_cache = {(pid, shiny): v
                        for (pid, shiny, sc), v in self._cache.items()
                        if sc == SCALE}
        StarterSelect(self.root, select_cache, STARTER_LINES,
                      self._change_line, quit_on_close=False)

    def _change_line(self, idx: int):
        self.line_idx  = idx
        self.evo_stage = 0
        if getattr(self, "unlocked", None) is not None:
            self.unlocked.add((idx, 0))
        self.is_shiny  = random.random() < (1 / SHINY_CHANCE)
        self.frame_i   = 0
        self._save_state()
        self._apply()
        self._build_menu()

    def _reroll_shiny(self):
        self.is_shiny = random.random() < (1 / SHINY_CHANCE)
        self.frame_i  = 0
        self._save_state()
        self._apply()

    # ── Collection book (收集册) ───────────────────────────────────────────────
    def _unlock_hint(self, line, si: int) -> str:
        """The unlock condition shown on a locked card."""
        if si == 0:
            return "选为初始伙伴"
        if line is STARTER_LINES[self.EEVEE_LINE]:
            req = line["evolutions"][si].get("req", "")
            if req.startswith("stone:"):
                return req.split(":", 1)[1]
            return "亲密度"
        return "进化前一只"

    def _open_collection(self):
        """The card album: every form in the game, unlocked ones
        face up (sprite + name), locked ones face down with the
        unlock hint -- the 'collect the rest' goal made visible."""
        win = tk.Toplevel(self.root)
        win.title("EeveeMon — Collection 收集册")
        win.resizable(True, True)
        c = tk.Canvas(win, width=560, height=600, bg="#0E1F09",
                      highlightthickness=0)
        c.pack(fill="both", expand=True)
        CW, CH, PAD, COLS = 108, 116, 8, 5
        col = row = total = 0
        self._album_imgs = []
        for li, line in enumerate(STARTER_LINES):
            for si, ev in enumerate(line["evolutions"]):
                key = (li, si)
                have = key in self.unlocked
                x0 = PAD + col * CW
                y0 = 34 + row * CH
                x1, y1 = x0 + CW - PAD, y0 + CH - PAD
                c.create_rectangle(
                    x0, y0, x1, y1,
                    fill="#162412" if have else "#0B1A08",
                    outline="#C9A227" if have else "#2A3A20",
                    width=2 if have else 1)
                if have:
                    path = sprite_path(ev["id"], False)
                    if os.path.exists(path):
                        frames_r, frames_l, _w, _h = load_frames(
                            path, scale=2, keyout_bg="#162412")
                        # hold refs to BOTH mirrored lists -- Tk
                        # collects un-referenced PhotoImages
                        self._album_imgs.extend(frames_r)
                        self._album_imgs.extend(frames_l)
                        c.create_image((x0 + x1) // 2,
                                       y0 + 34, image=frames_r[0])
                    c.create_text((x0 + x1) // 2, y1 - 14,
                                  text=ev["name"], fill="#FFFFFF",
                                  font=("Segoe UI", 8, "bold"))
                else:
                    c.create_text((x0 + x1) // 2, y0 + 36,
                                  text="?", fill="#4A6840",
                                  font=("Segoe UI", 20, "bold"))
                    c.create_text((x0 + x1) // 2, y1 - 14,
                                  text=self._unlock_hint(line, si),
                                  fill="#4A6840",
                                  font=("Segoe UI", 7))
                total += 1
                col += 1
                if col >= COLS:
                    col = 0
                    row += 1
        got = len(self.unlocked)
        c.create_text(280, 16,
                      text=f"Collection {got}/{total} — 进化与切换即解锁",
                      fill="#A8C898", font=("Segoe UI", 11, "bold"))
        try:
            win.attributes("-topmost", True)
            win.lift()
        except tk.TclError:
            pass

    def _change_size(self, pct: int):
        self.size_pct = pct
        self.frame_i  = 0
        self._save_state()
        self._apply()
        self._build_menu()

    # ── Right-click menu ──────────────────────────────────────────────────────
    def _build_menu(self):
        line = STARTER_LINES[self.line_idx]
        evo  = line["evolutions"][self.evo_stage]
        name = evo["name"] + ("  [Shiny!]" if self.is_shiny else "")

        if hasattr(self, "_menu"):
            self._menu.destroy()

        m = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 9))
        m.add_command(label=name, state="disabled",
                      font=("Segoe UI", 9, "bold"))
        m.add_separator()

        # Evolution
        n_stage = len(line["evolutions"])
        if self.line_idx == self.EEVEE_LINE:
            sub_e = tk.Menu(m, tearoff=0, font=("Segoe UI", 9))
            for i, ev in enumerate(line["evolutions"][1:], start=1):
                sub_e.add_command(label=self._evo_label(ev),
                                  state="normal" if self._evo_available(ev)
                                  else "disabled",
                                  command=lambda s=i: self._evolve_to(s))
            m.add_cascade(label="Evolve", menu=sub_e)
        else:
            m.add_command(
                label="Evolve",
                command=self._evolve,
                state="normal" if self.evo_stage < n_stage - 1
                else "disabled",
            )
        m.add_command(
            label="Devolve",
            command=self._devolve,
            state="normal" if self.evo_stage > 0 else "disabled",
        )
        rem = max(0, int(self._gift_until - time.time()))
        m.add_command(
            label=("Gift 进化石" if rem == 0
                   else f"Gift 进化石 (冷却 {rem // 60}:{rem % 60:02d})"),
            state="normal" if rem == 0 else "disabled",
            command=self._gift)
        m.add_separator()

        # Moves
        sub_m = tk.Menu(m, tearoff=0, font=("Segoe UI", 9))
        for mv in line["moves"]:
            sub_m.add_command(label=mv["name"],
                              command=lambda fx=mv["fx"]: self._use_move(fx))
        m.add_cascade(label="Use Move", menu=sub_m)

        # Change starter
        sub_s = tk.Menu(m, tearoff=0, font=("Segoe UI", 9))
        for i, ln in enumerate(STARTER_LINES):
            mark = "●  " if i == self.line_idx else "    "
            sub_s.add_command(
                label=f"{mark}{ln['evolutions'][0]['name']}",
                command=lambda idx=i: self._change_line(idx),
            )
        m.add_cascade(label="Change Starter", menu=sub_s)
        m.add_command(label="选择界面 (Start Menu)",
                      command=self._open_select)
        m.add_command(label="Collection 收集册",
                      command=self._open_collection)

        # Size
        sub_z = tk.Menu(m, tearoff=0, font=("Segoe UI", 9))
        for pct in SIZE_OPTIONS:
            mark = "●  " if pct == self.size_pct else "    "
            sub_z.add_command(
                label=f"{mark}{pct}%",
                command=lambda p=pct: self._change_size(p),
            )
        m.add_cascade(label="Change Size", menu=sub_z)

        # AI companion
        ai_on = self.agent is not None and self.agent._client is not None
        m.add_separator()
        m.add_command(label="Talk to Me",
                      command=lambda: self.agent.speak() if self.agent else None,
                      state="normal" if ai_on else "disabled")
        m.add_command(label="Chat 输入…",
                      command=self._open_chat_input,
                      state="normal" if ai_on else "disabled")
        m.add_command(label="Look Around",
                      command=lambda: self.agent.look_around() if self.agent else None,
                      state="normal" if ai_on else "disabled")

        m.add_separator()
        m.add_command(label="Reroll Shiny", command=self._reroll_shiny)
        m.add_command(label="Throw Up",     command=self._throw)
        m.add_separator()
        m.add_command(label="Quit",
                      command=self._quit_app)

        self._menu = m

    def _quit_app(self):
        # destroy the root AFTER the menu has closed (destroying
        # from inside a posted menu's callback is unreliable on
        # Tk -- the 'cannot close' bug).  The os._exit fallback
        # guarantees the process never lingers.
        def _kill():
            try:
                self._save_state()
            except Exception:
                pass
            try:
                self.root.destroy()
            except tk.TclError:
                pass
            os._exit(0)
        self.root.after(60, _kill)

    def _show_menu(self, e):
        try:    self._menu.tk_popup(e.x_root, e.y_root)
        finally: self._menu.grab_release()

    # ── Moves ─────────────────────────────────────────────────────────────────
    def _use_move(self, fx: str):
        MoveEffect(self.root, int(self.x), int(self.y),
                   self.sw, self.sh, fx, self.facing)

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _press(self, e):
        self._drag_ox, self._drag_oy = e.x, e.y
        self._click_x0, self._click_y0 = e.x, e.y
        self._dragging = True
        self.vy = 0.0; self.state = "grounded"

    def _drag(self, e):
        if not self._dragging: return
        self.x += e.x - self._drag_ox
        self.y += e.y - self._drag_oy
        if self.y > self.ground_y: self.y = self.ground_y
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def _release(self, e):
        self._dragging = False
        # Treat as a click (not a drag) if mouse barely moved →
        # single click = random talk, DOUBLE click = the chat
        # input window (type to the pet)
        if abs(e.x - self._click_x0) < 6 and abs(e.y - self._click_y0) < 6:
            now = time.time()
            if getattr(self, "_last_click_t", 0) \
                    and now - self._last_click_t < 0.4:
                self._last_click_t = 0.0
                self._open_chat_input()
            else:
                self._last_click_t = now
                if self.agent:
                    self.agent.speak()

    # ── Chat input (type to the pet) ──────────────────────────────────────────
    def _open_chat_input(self):
        """A small input window in the selection-screen style
        (dark forest + gold): type a message, the pet replies in
        its speech bubble (and remembers the exchange)."""
        if not self.agent or self.agent._client is None:
            return
        win = tk.Toplevel(self.root)
        win.title("EeveeMon — Chat")
        win.resizable(False, False)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"380x120+{(sw-380)//2}+{(sh-120)//2}")
        win.attributes("-topmost", True)
        win.configure(bg="#0E1F09")
        # retro header
        tk.Label(win, text="说点什么吧，训练家！",
                 bg="#0E1F09", fg="#A8C898",
                 font=("Segoe UI", 11, "italic")).pack(pady=(12, 4))
        entry = tk.Entry(win, font=("Segoe UI", 11),
                         bg="#162412", fg="#FFFFFF",
                         insertbackground="#C9A227",
                         relief="flat")
        entry.pack(fill="x", padx=14, ipady=5)

        def send(_event=None):
            text = entry.get().strip()
            if text:
                self.agent._call(text)
            win.destroy()

        tk.Button(win, text="Send 发送", command=send,
                  bg="#6B5A2E", fg="#FFFFFF",
                  activebackground="#C9A227",
                  activeforeground="#FFFFFF",
                  relief="flat",
                  font=("Segoe UI", 10, "bold")).pack(pady=(10, 10))
        entry.bind("<Return>", send)
        entry.focus_set()

    # ── Actions ───────────────────────────────────────────────────────────────
    def _throw(self):
        # a little hop + a burst of bubbles (the visible fun part)
        self.vy = -16.0
        self.state = "falling"
        MoveEffect(self.root, int(self.x), int(self.y),
                   self.sw, self.sh, "bubble", self.facing)

    def _start_walk(self):
        self.state = "walk"
        # walk TOWARD the screen centre (no moonwalking away):
        # facing follows the movement direction
        centre = self.scr_w / 2
        if self.x > centre + 60:
            self.facing = -1
        elif self.x < centre - 60:
            self.facing = 1
        else:
            self.facing = random.choice([-1, 1])
        self.action_cd = random.randint(50, 110)   # short walks

    def _start_idle(self):
        self.state     = "grounded"
        self.action_cd = random.randint(240, 480)  # mostly quiet

    # ── Main loop ─────────────────────────────────────────────────────────────
    def _tick(self):
        if not self._dragging:
            self._physics()
            self._behaviour()
        self._render()
        # re-assert always-on-top: new windows (browsers, video
        # players) can steal the topmost slot
        self._tick_n = getattr(self, "_tick_n", 0) + 1
        if self._tick_n % 40 == 0:
            try:
                self.root.attributes("-topmost", True)
                self.root.lift()
            except tk.TclError:
                pass
        self.root.after(FRAME_MS, self._tick)

    def _physics(self):
        if self.state == "falling":
            self.vy += GRAVITY
            self.y  += self.vy
            if self.y >= self.ground_y:
                self.y = self.ground_y; self.vy = 0.0; self._start_idle()
            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
        elif self.state == "walk":
            self.x += self.facing * WALK_SPEED
            if self.x < 0:
                self.x = 0; self.facing = 1
            elif self.x > self.scr_w - self.sw:
                self.x = self.scr_w - self.sw; self.facing = -1
            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def _behaviour(self):
        if self.state == "falling": return
        self.action_cd -= 1
        if self.action_cd <= 0:
            if random.random() < 0.2: self._start_walk()   # mostly idle
            else: self._start_idle()

    def _render(self):
        self.frame_i = (self.frame_i + 1) % self.n_frames
        frame = (self.frames_r if self.facing == 1 else self.frames_l)[self.frame_i]
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=frame)


# ═══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    Buddy()
