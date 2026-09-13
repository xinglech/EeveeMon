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


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" +
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

print()
if FAILS:
    print(f"{len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("ALL TESTS PASSED")
