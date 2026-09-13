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
import urllib.request, os, sys, time, random, math, threading, base64, io, textwrap, json

# ═══════════════════════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════════════════════
if getattr(sys, "frozen", False):
    DIR = os.path.join(sys._MEIPASS, "sprites")   # bundled in the exe
else:
    DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprites")
os.makedirs(DIR, exist_ok=True)

TRANSPARENT  = "#FF00FF"
TASKBAR_H    = 48
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
        if keyout_bg is None:
            # taskbar path: snap near-magenta anti-aliased edges to
            # the exact colour key so no pink fringe survives
            px = fr.load()
            for yy in range(fr.height):
                for xx in range(fr.width):
                    r, g, b, a = px[xx, yy]
                    if a > 0 and r > 200 and g < 100 and b > 200:
                        px[xx, yy] = (255, 0, 255, a)
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
        self.win.attributes("-transparentcolor", TRANSPARENT)
        self.win.configure(bg=TRANSPARENT)
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
    """
    Animated starter selection screen.
    Three cards on a wooden lab table; click one to begin.
    """
    W, H      = 1090, 430
    CARD_TOP  = 82
    CARD_BOT  = 340
    SLOT_CX   = (120, 340, 560, 780, 1000)

    def __init__(self, root, cache: dict, lines: list, callback):
        self.root     = root
        self.cache    = cache      # {(pid, shiny): (rights, lefts, w, h)}
        self.lines    = lines
        # key out the magenta sprite background and composite over
        # the card colour for the selection screen
        keyed = {}
        for (pid, shiny), v in self.cache.items():
            path = sprite_path(pid, shiny)
            if os.path.exists(path):
                keyed[(pid, shiny)] = load_frames(
                    path, scale=SCALE, keyout_bg="#162412")
        if keyed:
            self.cache = keyed
        self.callback = callback   # callback(line_idx: int)
        self.hover    = -1
        self.frame    = 0
        self.done     = False

        # Static background stars / foliage dots
        self.stars = [
            (random.randint(0, self.W), random.randint(0, 270),
             random.choice(["#2D4E1F", "#3A6A2A", "#1E3A14", "#4A7A30"]))
            for _ in range(60)
        ]

        self.win = tk.Toplevel(root)
        self.win.title("EeveeMon — Choose your starter!")
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._quit)

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(
            f"{self.W}x{self.H}"
            f"+{(sw - self.W) // 2}+{(sh - self.H) // 2}"
        )

        self.c = tk.Canvas(self.win, width=self.W, height=self.H,
                           bg="#0E1F09", highlightthickness=0)
        self.c.pack()
        self.c.bind("<Motion>",   self._on_motion)
        self.c.bind("<Button-1>", self._on_click)

        self._tick()

    # ── Events ────────────────────────────────────────────────────────────────
    @staticmethod
    def _quit():
        sys.exit(0)

    def _on_motion(self, e):
        new = -1
        for i, cx in enumerate(self.SLOT_CX):
            if abs(e.x - cx) < 82 and self.CARD_TOP < e.y < self.CARD_BOT:
                new = i; break
        self.hover = new

    def _on_click(self, e):
        if self.done:
            return
        for i, cx in enumerate(self.SLOT_CX):
            if abs(e.x - cx) < 82 and self.CARD_TOP < e.y < self.CARD_BOT:
                self.done = True
                self._flash(i)
                return

    def _flash(self, idx: int):
        self.c.create_rectangle(0, 0, self.W, self.H, fill="#FFFFFF", outline="")
        self.win.update()
        self.win.after(110, lambda: self._finish(idx))

    def _finish(self, idx: int):
        self.callback(idx)
        self.win.destroy()

    # ── Colour helper ─────────────────────────────────────────────────────────
    @staticmethod
    def _dim(hex_col: str, factor: float = 0.4) -> str:
        r = max(0, min(255, int(int(hex_col[1:3], 16) * factor)))
        g = max(0, min(255, int(int(hex_col[3:5], 16) * factor)))
        b = max(0, min(255, int(int(hex_col[5:7], 16) * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ── Draw loop ─────────────────────────────────────────────────────────────
    def _tick(self):
        if self.done or not self.win.winfo_exists():
            return

        c, f = self.c, self.frame
        c.delete("all")

        # Background
        c.create_rectangle(0, 0, self.W, self.H, fill="#0E1F09", outline="")
        for sx, sy, sc in self.stars:
            c.create_oval(sx - 1, sy - 1, sx + 1, sy + 1, fill=sc, outline="")

        # Wooden table
        c.create_rectangle(0, 355, self.W, self.H,  fill="#2D1505", outline="")
        c.create_rectangle(0, 355, self.W, 369,      fill="#4A2008", outline="")
        c.create_rectangle(0, 369, self.W, 380,      fill="#6B3510", outline="")
        c.create_rectangle(0, 380, self.W, self.H,  fill="#3D2008", outline="")
        for gx in range(0, self.W, 58):
            c.create_line(gx, 369, gx + 38, self.H, fill="#321A06", width=1)

        # Title  (drop-shadow effect)
        for dx, dy, col in ((2, 2, "#7A5800"), (0, 0, "#FFD700")):
            c.create_text(self.W // 2 + dx, 27 + dy,
                          text="BuddyMon",
                          fill=col, font=("Consolas", 24, "bold"))
        c.create_text(self.W // 2, 55,
                      text="Choose your starter, trainer!",
                      fill="#A8C898", font=("Segoe UI", 12, "italic"))

        # ── Cards ─────────────────────────────────────────────────────────────
        ct, cb = self.CARD_TOP, self.CARD_BOT

        for i, (cx, line) in enumerate(zip(self.SLOT_CX, self.lines)):
            col = line["color"]
            hov = (i == self.hover)

            # Outer glow when hovered
            if hov:
                for expand, bg_col in (
                    (20, "#142010"), (14, "#1C3018"), (8, "#243820")
                ):
                    c.create_rectangle(
                        cx - 80 - expand, ct - expand,
                        cx + 80 + expand, cb + expand,
                        fill=bg_col, outline="",
                    )

            # Card body
            c.create_rectangle(cx - 80, ct, cx + 80, cb,
                               fill="#1A3015" if hov else "#131E0F",
                               outline="")

            # Card border (type colour)
            c.create_rectangle(cx - 80, ct, cx + 80, cb,
                               fill="", outline=col if hov else self._dim(col, 0.55),
                               width=3 if hov else 2)

            # Bottom type strip
            strip = col if hov else self._dim(col, 0.6)
            c.create_rectangle(cx - 80, cb - 46, cx + 80, cb,
                               fill=strip, outline="")

            # Pokémon name
            evo0 = line["evolutions"][0]
            c.create_text(cx, cb - 30,
                          text=evo0["name"],
                          fill="#FFFFFF" if hov else "#CCCCCC",
                          font=("Segoe UI", 10, "bold"))

            # Type label
            c.create_text(cx, cb - 13,
                          text=line["type"],
                          fill="#FFFFFF",
                          font=("Segoe UI", 8))

            # Animated sprite with bob
            pid = evo0["id"]
            if (pid, False) in self.cache:
                frames_r, _, sw_, sh_ = self.cache[(pid, False)]
                fidx = f % len(frames_r)
                bob  = int(math.sin(f * 0.12 + i * 2.1) * 6)
                # Centre sprite in the Pokemon area (above strip)
                sprite_cy = (ct + cb - 46) // 2
                c.create_image(
                    cx - sw_ // 2,
                    sprite_cy - sh_ // 2 + bob,
                    anchor="nw", image=frames_r[fidx],
                )

        # Footer hint
        c.create_text(self.W // 2, self.H - 10,
                      text="Click a Pokémon to begin",
                      fill="#4A6840", font=("Segoe UI", 9))

        self.frame += 1
        self.win.after(FRAME_MS, self._tick)


# ═══════════════════════════════════════════════════════════════════════════════
#  Chat Bubble
# ═══════════════════════════════════════════════════════════════════════════════
class ChatBubble:
    """Speech bubble that appears above/below the sprite with the AI response."""
    W    = 290
    PAD  = 14
    TAIL = 14
    LIFE = 8000   # ms before auto-dismiss

    def __init__(self, root, sx: int, sy: int, sw: int, sh: int,
                 name: str, col: str, text: str):
        wrapped = textwrap.fill(text, width=32)

        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", TRANSPARENT)
        self.win.configure(bg=TRANSPARENT)
        for attr in ("-toolwindow",):
            try: self.win.wm_attributes(attr, True)
            except tk.TclError: pass

        # Measure wrapped text height with a temp label
        _m = tk.Label(self.win, text=wrapped, font=("Segoe UI", 10),
                      wraplength=self.W - self.PAD * 2, justify="left")
        _m.pack(); self.win.update_idletasks()
        th = _m.winfo_reqheight(); _m.destroy()

        name_h  = 20
        body_h  = self.PAD + name_h + 6 + th + self.PAD
        total_h = body_h + self.TAIL

        scr_w = root.winfo_screenwidth()
        bx    = max(8, min(sx + sw // 2 - self.W // 2, scr_w - self.W - 8))
        above = (sy - total_h - 6) > 8
        by    = (sy - total_h - 6) if above else (sy + sh + 6)

        self.win.geometry(f"{self.W}x{total_h}+{bx}+{by}")
        c = tk.Canvas(self.win, width=self.W, height=total_h,
                      bg=TRANSPARENT, highlightthickness=0)
        c.pack()

        tx = self.W // 2   # tail x-centre

        if above:
            # Bubble body, tail below
            c.create_rectangle(0, 0, self.W, body_h, fill=col, outline="")
            c.create_rectangle(2, 2, self.W - 2, body_h - 2, fill="#1E1E20", outline="")
            c.create_polygon(tx - 10, body_h, tx + 10, body_h, tx, total_h,
                             fill=col, outline="")
            text_y0 = self.PAD
        else:
            # Tail above, bubble body below
            c.create_polygon(tx - 10, 0, tx + 10, 0, tx, self.TAIL,
                             fill=col, outline="")
            c.create_rectangle(0, self.TAIL, self.W, total_h, fill=col, outline="")
            c.create_rectangle(2, self.TAIL + 2, self.W - 2, total_h - 2,
                               fill="#1E1E20", outline="")
            text_y0 = self.TAIL + self.PAD

        # Name
        c.create_text(self.PAD, text_y0, text=name, fill=col,
                      font=("Segoe UI", 9, "bold"), anchor="nw")
        # Divider
        c.create_line(self.PAD, text_y0 + name_h + 1,
                      self.W - self.PAD, text_y0 + name_h + 1,
                      fill=col, width=1)
        # Message
        c.create_text(self.PAD, text_y0 + name_h + 8, text=wrapped,
                      fill="#F0F0F0", font=("Segoe UI", 10),
                      anchor="nw", width=self.W - self.PAD * 2, justify=tk.LEFT)

        self.win.bind("<Button-1>", lambda e: self._dismiss())
        self.win.deiconify()
        self.win.after(self.LIFE, self._dismiss)

    def _dismiss(self):
        try: self.win.destroy()
        except tk.TclError: pass


# ═══════════════════════════════════════════════════════════════════════════════
#  Agent Mind — Claude-powered companion
# ═══════════════════════════════════════════════════════════════════════════════
class AgentMind:
    """Gives the Pokémon buddy a personality and screen awareness via Claude."""

    MODEL = "claude-haiku-4-5-20251001"

    def __init__(self, buddy):
        self.buddy   = buddy
        self._client = None
        self._setup()

    def _app_dir(self) -> str:
        # next to the exe when frozen, else the script dir
        if getattr(sys, "frozen", False):
            return os.path.dirname(os.path.abspath(sys.executable))
        return os.path.dirname(os.path.abspath(__file__))

    def _load_config(self):
        """provider.txt: line 1 = provider (deepseek/openai/
        anthropic, default deepseek), line 2 = model (optional).
        Key from apikey.txt / deepseek_key.txt next to the app."""
        d = self._app_dir()
        provider, model = "deepseek", ""
        pf = os.path.join(d, "provider.txt")
        if os.path.exists(pf):
            lines = [l.strip() for l in
                     open(pf, encoding="utf-8").read().splitlines()]
            if lines and lines[0]:
                provider = lines[0].lower()
            if len(lines) > 1 and lines[1]:
                model = lines[1]
        key = ""
        for kf in ("apikey.txt", "deepseek_key.txt"):
            fp = os.path.join(d, kf)
            if os.path.exists(fp):
                key = open(fp, encoding="utf-8").read().strip()
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
                    "messages": [{"role": "user",
                                  "content": prompt}],
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
            self.buddy.root.after(0, lambda: self._show(text))
        except Exception as exc:
            print(f"[AgentMind] {exc}", flush=True)

    def _look_thread(self):
        try:
            from PIL import ImageGrab
            shot = ImageGrab.grab()
            shot = shot.resize((1280, 720), Image.LANCZOS)
            buf  = io.BytesIO()
            shot.save(buf, format="PNG")
            img_b64 = base64.standard_b64encode(buf.getvalue()).decode()

            # deepseek-chat is text-only: no vision payload; fall
            # back to an in-character guess about the screen
            self.buddy.root.after(0, lambda: self._show(
                "（偷偷看了一眼你的屏幕，只看到一堆发光的方块。）"))
            return
        except Exception as exc:
            print(f"[AgentMind look] {exc}", flush=True)

    def _show(self, text: str):
        line = STARTER_LINES[self.buddy.line_idx]
        evo  = line["evolutions"][self.buddy.evo_stage]
        ChatBubble(self.buddy.root,
                   int(self.buddy.x), int(self.buddy.y),
                   self.buddy.sw, self.buddy.sh,
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
        # evolution-stone inventory (the light item system)
        self.inventory = {"水之石": 1, "雷之石": 1, "火之石": 1,
                          "叶之石": 1, "冰之石": 1}
        self._gift_until = 0.0   # Gift cooldown deadline

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

        # Show starter selection
        select = StarterSelect(self.root, _select_cache, STARTER_LINES, self._on_chosen)
        self.root.wait_window(select.win)

        if not getattr(self, "_started", False):
            return  # window closed without choosing

        # ── Configure root as the buddy window ────────────────────────────────
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", TRANSPARENT)
        self.root.configure(bg=TRANSPARENT)
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
        self.root.after(4000, self.agent.greet)  # greet after landing

        self._tick()
        self.root.mainloop()

    # ── Starter selection callback ────────────────────────────────────────────
    def _on_chosen(self, line_idx: int):
        self.line_idx  = line_idx
        self.evo_stage = 0
        self.is_shiny  = random.random() < (1 / SHINY_CHANCE)
        self._started  = True

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
        self.frame_i = 0
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
            self._apply()
            self._evo_flash()
            self._build_menu()
            return
        if self.evo_stage > 0:
            self.evo_stage -= 1
            self.frame_i = 0
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
    def _change_line(self, idx: int):
        self.line_idx  = idx
        self.evo_stage = 0
        self.is_shiny  = random.random() < (1 / SHINY_CHANCE)
        self.frame_i   = 0
        self._apply()
        self._build_menu()

    def _reroll_shiny(self):
        self.is_shiny = random.random() < (1 / SHINY_CHANCE)
        self.frame_i  = 0
        self._apply()

    def _change_size(self, pct: int):
        self.size_pct = pct
        self.frame_i  = 0
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
        m.add_command(label="Look Around",
                      command=lambda: self.agent.look_around() if self.agent else None,
                      state="normal" if ai_on else "disabled")

        m.add_separator()
        m.add_command(label="Reroll Shiny", command=self._reroll_shiny)
        m.add_command(label="Throw Up",     command=self._throw)
        m.add_separator()
        m.add_command(label="Quit",         command=self.root.destroy)

        self._menu = m

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
        # Treat as a click (not a drag) if mouse barely moved → talk
        if abs(e.x - self._click_x0) < 6 and abs(e.y - self._click_y0) < 6:
            if self.agent:
                self.agent.speak()

    # ── Actions ───────────────────────────────────────────────────────────────
    def _throw(self):
        self.vy = -16.0; self.state = "falling"

    def _start_walk(self):
        self.state     = "walk"
        self.facing    = random.choice([-1, 1])
        self.action_cd = random.randint(80, 200)

    def _start_idle(self):
        self.state     = "grounded"
        self.action_cd = random.randint(60, 160)

    # ── Main loop ─────────────────────────────────────────────────────────────
    def _tick(self):
        if not self._dragging:
            self._physics()
            self._behaviour()
        self._render()
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
            if random.random() < 0.6: self._start_walk()
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
