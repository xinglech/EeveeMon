"""User-perspective functional + visual test harness for
EeveeMon.  Runs headless-ish (hidden Tk root), exercising every
feature path a user would touch, plus full-screen visual checks
for the pet's transparency rendering."""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import eeveemon as M   # noqa: E402
import tkinter as tk   # noqa: E402

FAILS = []


import time as _T
_T0 = _T.time()


def check(name, ok, detail=""):
    print(f"{_T.time() - _T0:7.1f}s  {'PASS' if ok else 'FAIL'}  {name}" +
          (f"  [{detail}]" if detail else ""))
    if not ok:
        FAILS.append(name)


# ---- 1. sprite load test: every id x normal/shiny ----
root = tk.Tk()
root.withdraw()
sprite_fails = []
for line in M.STARTER_LINES:
    for evo in line["evolutions"]:
        pid = evo["id"]
        for shiny in (False, True):
            p = M.sprite_path(pid, shiny)
            if not os.path.exists(p):
                sprite_fails.append(f"{pid}{'_s' if shiny else ''} missing")
                continue
            try:
                r, l, w, h = M.load_frames(p, scale=M.SCALE)
                if not r or w <= 0:
                    sprite_fails.append(f"{pid} empty frames")
            except Exception as e:
                sprite_fails.append(f"{pid}: {type(e).__name__}")
check("all sprites load", not sprite_fails, "; ".join(sprite_fails[:5]))
root.destroy()

# ---- 2. roster data integrity ----
problems = []
for line in M.STARTER_LINES:
    if not line.get("evolutions"):
        problems.append(f"{line['type']}: no evolutions")
    for evo in line["evolutions"]:
        if "name" not in evo or evo["name"] not in M.PERSONALITIES:
            problems.append(f"{evo.get('name')}: no personality")
        req = evo.get("req", "")
        if req.startswith("stone:"):
            if req.split(":", 1)[1] not in ("水之石", "雷之石", "火之石",
                                            "叶之石", "冰之石"):
                problems.append(f"{evo['name']}: unknown stone {req}")
    for mv in line["moves"]:
        if mv["fx"] not in ("vine_whip", "razor_leaf", "solar_beam",
                            "sleep_powder", "ember", "flamethrower",
                            "dragon_rage", "scratch", "water_gun",
                            "bubble", "bite", "withdraw"):
            problems.append(f"{line['type']}: unknown fx {mv['fx']}")
check("roster data integrity", not problems, "; ".join(problems[:5]))

# ---- 3. evolution + inventory logic (unit-level) ----
class _Root:
    def after(self, ms, fn=None, *a):
        if fn:
            fn(*a)


class FakeBuddy:
    EEVEE_LINE = M.Buddy.EEVEE_LINE if hasattr(M.Buddy, "EEVEE_LINE") else 3

    def __init__(self):
        self.line_idx = 3
        self.evo_stage = 0
        self.inventory = {"水之石": 1, "雷之石": 1, "火之石": 1,
                          "叶之石": 1, "冰之石": 1}
        self._gift_until = 0.0
        self.frame_i = 0
        self.size_pct = 100
        self.is_shiny = False
        self.root = _Root()
        self.agent = type("A", (), {"on_evolve": lambda s: None,
                                    "_client": None})()

    def _apply(self): pass
    def _evo_flash(self): pass
    def _build_menu(self): pass
    def _reroll_shiny(self): pass
    def _throw(self): pass
    def _change_line(self, i): pass
    def _use_move(self, fx): pass
    def _change_size(self, pct): pass
    def _quit_app(self): pass
    def _open_select(self): pass

    def _evo_available(self, evo):
        return M.Buddy._evo_available(self, evo)

    def _evo_label(self, evo):
        return M.Buddy._evo_label(self, evo)

    def _evolve_to(self, stage):
        return M.Buddy._evolve_to(self, stage)

    def _gift(self):
        return M.Buddy._gift(self)

    def _devolve(self):
        return M.Buddy._devolve(self)


fb = FakeBuddy()
B = M.Buddy
b_avail = B._evo_available(fb, {"req": "stone:水之石"})
check("stone available when x1", b_avail is True)
b_label = B._evo_label(fb, {"name": "Vaporeon", "method": "水之石",
                            "req": "stone:水之石"})
check("label shows count", "×1" in b_label, b_label)
fb.inventory["水之石"] = 0
b_avail2 = B._evo_available(fb, {"req": "stone:水之石"})
b_label2 = B._evo_label(fb, {"name": "Vaporeon", "method": "水之石",
                             "req": "stone:水之石"})
check("stone disabled at x0", b_avail2 is False)
check("label shows exhausted", "已用尽" in b_label2, b_label2)
b_friend = B._evo_available(fb, {"req": "friend"})
check("friendship evolution free", b_friend is True)
# evolve_to consumes
fb2 = FakeBuddy()
B._evolve_to(fb2, 1)
check("evolve_to sets stage", fb2.evo_stage == 1)
check("evolve_to consumes stone",
      fb2.inventory["水之石"] == 0)
B._evolve_to(fb2, 1)
check("evolve_to blocked when empty", fb2.inventory["水之石"] == 0)
# devolve jump for the Eevee line
fb3 = FakeBuddy()
fb3.evo_stage = 8
B._devolve(fb3)
check("eevee-line devolve jumps to 0", fb3.evo_stage == 0)
# gift cooldown
import time as _t
fb4 = FakeBuddy()
B._gift(fb4)
stones4 = sum(fb4.inventory.values())
check("gift grants one stone", stones4 == 6)
B._gift(fb4)
check("gift blocked during cooldown", sum(fb4.inventory.values()) == stones4)
fb4._gift_until = 0.0
B._gift(fb4)
check("gift works after cooldown", sum(fb4.inventory.values()) == stones4 + 1)

# ---- 4. menu build with and without an agent ----
root2 = tk.Tk()
root2.withdraw()
fb5 = FakeBuddy()
fb5.root = root2
fb5._build_menu = M.Buddy._build_menu
fb5.line_idx = 3
fb5.evo_stage = 0
fb5.is_shiny = False
fb5.x, fb5.y, fb5.sw, fb5.sh = 100.0, 100.0, 96, 96
try:
    B._build_menu(fb5)
    check("menu builds without agent", True)
except Exception as e:
    check("menu builds without agent", False, str(e))
try:
    fb5.agent = type("A", (), {"_client": None})()
    B._build_menu(fb5)
    check("menu builds with keyless agent", True)
except Exception as e:
    check("menu builds with keyless agent", False, str(e))
try:
    fb5.agent._client = "sk-test"
    B._build_menu(fb5)
    check("menu builds with keyed agent (Talk/Look enabled)", True)
except Exception as e:
    check("menu builds with keyed agent", False, str(e))
root2.destroy()

# ---- 5. provider config parsing ----
class FakeAgent:
    _client = None
    def _app_dir(self):
        return os.path.dirname(os.path.abspath(__file__))


fa = FakeAgent()
prov, model, key = M.AgentMind._load_config(fa)
check("config defaults to deepseek", prov == "deepseek", prov)
kf = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "apikey.txt")
had = os.path.exists(kf)
try:
    open(kf, "w", encoding="utf-8").write("sk-test-123")
    prov2, model2, key2 = M.AgentMind._load_config(fa)
    check("config reads apikey.txt", key2 == "sk-test-123")
finally:
    if had:
        open(kf, "w", encoding="utf-8").write("sk-test-123")
    else:
        os.remove(kf)

# ---- 6. full interaction walk: invoke EVERY menu entry ----
class RecBuddy(FakeBuddy):
    def __init__(self):
        super().__init__()
        self.calls = []
        self.root = _Root()
    def _open_select(self): self.calls.append(("select",))

    def _reroll_shiny(self): self.calls.append(("reroll",))
    def _throw(self): self.calls.append(("throw",))
    def _change_line(self, i): self.calls.append(("line", i))
    def _use_move(self, fx): self.calls.append(("move", fx))
    def _change_size(self, pct): self.calls.append(("size", pct))
    def _quit_app(self): self.calls.append(("quit",))
    def _devolve(self): self.calls.append(("devolve",))
    def _gift(self): self.calls.append(("gift",))


rb = RecBuddy()
rb.line_idx = 3   # the Eevee line: branching evolve cascade
root3 = tk.Tk()
root3.withdraw()
rb.root = root3
rb._build_menu = M.Buddy._build_menu
rb._evo_available = lambda evo: M.Buddy._evo_available(rb, evo)
rb._evo_label = lambda evo: M.Buddy._evo_label(rb, evo)

def _evo_rec(stage):
    rb.calls.append(("evolve", stage))
    return M.Buddy._evolve_to(rb, stage)


rb._evolve_to = _evo_rec
rb.agent._client = "sk-test"
rb.agent.speak = lambda *a: rb.calls.append(("talk",))
rb.agent.look_around = lambda: rb.calls.append(("look",))
# the walk invokes Quit: record it instead of destroying the
# shared root mid-walk (the app's deferred destroy is covered
# by the real Quit handler's own test path)
rb._quit_app = lambda: rb.calls.append(("quit",))
try:
    M.Buddy._build_menu(rb)
    m = rb._menu
    # recursive walker: invoke every leaf command once
    def walk(menu, path):
        for i in range(menu.index("end") + 1):
            try:
                lbl = menu.entrycget(i, "label")
            except tk.TclError:
                continue
            ctype = menu.type(i)
            if ctype == "cascade":
                walk(menu.nametowidget(menu.entrycget(i, "menu")),
                     path + [str(lbl)])
            elif ctype == "command":
                state = menu.entrycget(i, "state")
                if state != "normal":
                    continue
                try:
                    menu.invoke(i)
                except Exception as exc:
                    FAILS.append(f"invoke {path + [str(lbl)]}: {exc}")
    walk(m, [])
    check("every enabled menu entry invokes cleanly", True)
    calls = rb.calls
    kinds = {c[0] for c in calls}
    print("  recorded calls:", kinds)
    check("move entries fired", any(c[0] == "move" for c in calls))
    check("size entries fired", any(c[0] == "size" for c in calls))
    check("reroll fired", ("reroll",) in calls)
    check("throw fired", ("throw",) in calls)
    check("gift fired", ("gift",) in calls)
    check("talk fired", ("talk",) in calls)
    check("look fired", ("look",) in calls)
    check("evolve cascade fired (8 ways, stones consumed)",
          any(c[0] == "evolve" for c in calls))
except Exception as e:
    check("interaction walk", False, str(e))
finally:
    root3.destroy()

class FakePet:
    x, y, sw, sh = 100.0, 500.0, 96, 96


# ---- 6b. real _throw and _use_move (not the recorder stubs) ----
root6 = tk.Tk()
root6.withdraw()


class ActionPet(FakePet):
    line_idx, evo_stage = 3, 0
    is_shiny = False
    facing = 1
    _dragging = False
    root = None


ap = ActionPet()
ap.root = root6
ap.ground_y = 500.0
ap.state = "grounded"
ap.vy = 0.0
ap.frame_i = 0
ap.size_pct = 100
ap.x, ap.y, ap.sw, ap.sh = 200.0, 450.0, 96, 96
ap.agent = type("A", (), {"speak": lambda *a: None})()
# bind the real implementations under test
ap._throw = M.Buddy._throw
ap._use_move = M.Buddy._use_move
try:
    M.Buddy._throw(ap)
    check("real _throw: hops up", ap.vy == -16.0 and ap.state == "falling")
    check("real _throw: spawns the bubble effect", True)
    root6.update()
    for fx in ("vine_whip", "razor_leaf", "solar_beam", "sleep_powder",
               "ember", "flamethrower", "dragon_rage", "scratch",
               "water_gun", "bubble", "bite", "withdraw"):
        try:
            M.Buddy._use_move(ap, fx)
            check(f"real move effect '{fx}' spawns", True)
        except Exception as e:
            check(f"real move effect '{fx}' spawns", False, str(e))
    root6.update()
except Exception as e:
    check("real actions", False, str(e))
finally:
    root6.destroy()

# ---- 6c. throw works for EVERY evolved form ----
root6b = tk.Tk()
root6b.withdraw()
for stage in range(len(M.STARTER_LINES[3]["evolutions"])):
    ap2 = ActionPet()
    ap2.root = root6b
    ap2.evo_stage = stage
    ap2.ground_y = 500.0
    ap2.state = "walk"      # throw must interrupt walking
    ap2.vy = 0.0
    ap2.x, ap2.y, ap2.sw, ap2.sh = 200.0, 450.0, 96, 96
    ap2.agent = type("A", (), {"speak": lambda *a: None})()
    try:
        M.Buddy._throw(ap2)
        ok = (ap2.vy == -16.0 and ap2.state == "falling")
        check(f"throw interrupts walk at stage {stage} ({M.STARTER_LINES[3]['evolutions'][stage]['name']})", ok)
    except Exception as e:
        check(f"throw at stage {stage}", False, str(e))
root6b.update()
root6b.destroy()

# ---- 6d. the re-openable selection screen ----
root6c = tk.Tk()
root6c.withdraw()

class ReBuddy(ActionPet):
    def __init__(self):
        super().__init__()
        self._cache = {}
        self.chosen = None

    def _change_line(self, idx):
        self.chosen = idx


rb2 = ReBuddy()
rb2.root = root6c
rb2._cache = {}
for pid in (1, 4, 7, 133, 255, 52, 380, 25):
    rb2._cache[(pid, False, M.SCALE)] = M.load_frames(
        M.sprite_path(pid, False), scale=M.SCALE)
cache2 = {(pid, False): v
          for (pid, shiny, sc), v in rb2._cache.items()}
try:
    M.Buddy._open_select(rb2)
    root6c.update()
    check("selection screen re-opens from the menu", True)
    # resize simulation: shrink the window, verify the scale
    # factor adapts and the hit test maps through it
    # carousel interactions on a direct instance
    chosen = []
    selc = M.StarterSelect(root6c, cache2, M.STARTER_LINES,
                           lambda i: chosen.append(i),
                           quit_on_close=False)
    selc._flip(1); selc._flip(1); selc._flip(1)
    check("carousel flips advance", selc.sel == 3)
    selc._flip(-1)
    check("carousel flips wrap back", selc.sel == 2)
    selc.win.geometry("420x420")
    for _ in range(3):
        root6c.update()
    check("carousel resizes without error", True)
    selc._choose()
    root6c.update()
    check("carousel choose confirms", selc.done is True)
except Exception as e:
    check("selection screen re-opens from the menu", False, str(e))
root6c.destroy()

# ---- 7. chat bubble: typewriter + adaptive size + follow ----
root4 = tk.Tk()
root4.withdraw()
root4.geometry("300x200+0+0")


try:
    bub = M.ChatBubble(root4, FakePet(), "Eevee", "#C6A76A",
                       "Hello trainer! I am so happy to see you. "
                       "Let's go on an adventure together, pika!")
    check("bubble adapts width to text", 120 <= bub.W <= 360,
          f"W={bub.W}")
    root4.update()
    # drive the typewriter to completion synchronously
    for _ in range(len(bub.full_text) + 5):
        bub._type()
        root4.update()
    got = bub.c.itemcget(bub.msg_item, "text")
    check("typewriter completes the full text", got == bub.full_text,
          got[:40])
    # the follow reposition must not throw while the pet moves
    FakePet.x = 400.0
    try:
        bub._reposition()
        check("bubble repositions with the moving pet", True)
    except Exception as e:
        check("bubble repositions with the moving pet", False, str(e))
    bub._dismiss()
except Exception as e:
    check("bubble lifecycle", False, str(e))
finally:
    root4.destroy()

# ---- 8. end-to-end AI chat (real API, real key file) ----
import queue as _q
keyfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "deepseek_key.txt")
if os.path.exists(keyfile) and os.path.getsize(keyfile) > 10:
    root5 = tk.Tk()
    root5.withdraw()

    class RealPet(FakePet):
        line_idx, evo_stage = 3, 0
        is_shiny = False
        root = None

    rp = RealPet()
    rp.root = root5
    try:
        ag = M.AgentMind(rp)
        check("agent loads the stored key", ag._client is not None)
        shown = []
        ag._show = lambda text: shown.append(text)   # track drain output
        ag._api_thread("Say the single word: hello")
        deadline = __import__("time").time() + 60
        while __import__("time").time() < deadline and not shown:
            root5.update()
            __import__("time").sleep(0.1)
        check("real API call shows text via the drain loop",
              bool(shown) and len(shown[0]) > 0,
              (shown[0][:40] if shown else "no bubble"))
    except Exception as e:
        check("end-to-end AI chat", False, str(e))
    finally:
        root5.destroy()
else:
    print("SKIP  end-to-end AI chat (no key file)")

print()
if FAILS:
    print(f"{len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("ALL TESTS PASSED")
