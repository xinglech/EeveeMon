"""Verify the right-click menu works for EVERY line/stage:
build the real menu for line_idx 0..7 and invoke every enabled
entry (recorded on stubs), then open the collection album for
each line.  Standalone complement to the test suite."""
import sys
import traceback
sys.path.insert(0, r"C:\Users\xinglechun\eeveemon")
import tkinter as tk
import eeveemon as M

FAILS = []


class FakeBuddy:
    EEVEE_LINE = M.Buddy.EEVEE_LINE

    def __init__(self):
        self.line_idx = 0
        self.evo_stage = 0
        self.inventory = {"水之石": 1, "雷之石": 1, "火之石": 1,
                          "叶之石": 1, "冰之石": 1}
        self._gift_until = 0.0
        self.frame_i = 0
        self.size_pct = 100
        self.is_shiny = False
        self.unlocked = {(0, 0)}
        self._album_imgs = []
        self.calls = []
        self.root = None
        self.agent = type("A", (), {"on_evolve": lambda s: None,
                                    "speak": lambda *a: None,
                                    "look_around": lambda: None,
                                    "_client": "sk-test"})()

    def _apply(self): pass
    def _evo_flash(self): pass
    def _build_menu(self): pass
    def _reroll_shiny(self): self.calls.append("reroll")
    def _throw(self): self.calls.append("throw")
    def _change_line(self, i): self.calls.append(f"line{i}")
    def _use_move(self, fx): self.calls.append(f"move")
    def _change_size(self, pct): self.calls.append(f"size{pct}")
    def _quit_app(self): self.calls.append("quit")
    def _open_select(self): self.calls.append("select")
    def _open_collection(self): self.calls.append("collection")
    def _open_chat_input(self): self.calls.append("chat_input")
    def _devolve(self): self.calls.append("devolve")
    def _gift(self): self.calls.append("gift")
    def _evolve(self): self.calls.append("evolve-linear")
    def _unlock_hint(self, line, si):
        return M.Buddy._unlock_hint(self, line, si)
    def _album_photo(self, path):
        return M.Buddy._album_photo(self, path)
    def _album_silhouette(self, path):
        return M.Buddy._album_silhouette(self, path)
    ALBUM_BOX = (78, 58)


root = tk.Tk()
root.withdraw()

for li in range(len(M.STARTER_LINES)):
    fb = FakeBuddy()
    fb.line_idx = li
    fb.root = root
    fb._build_menu = M.Buddy._build_menu
    fb._evo_available = lambda evo: M.Buddy._evo_available(fb, evo)
    fb._evo_label = lambda evo: M.Buddy._evo_label(fb, evo)
    fb._evolve_to = lambda stage: fb.calls.append(f"evolve{stage}")
    try:
        M.Buddy._build_menu(fb)
        m = fb._menu

        def walk(menu, path):
            for i in range(menu.index("end") + 1):
                try:
                    lbl = menu.entrycget(i, "label")
                    ctype = menu.type(i)
                except tk.TclError:
                    continue
                if ctype == "cascade":
                    walk(menu.nametowidget(menu.entrycget(i, "menu")),
                         path + [str(lbl)])
                elif ctype == "command":
                    if menu.entrycget(i, "state") != "normal":
                        continue
                    try:
                        menu.invoke(i)
                    except Exception as exc:
                        FAILS.append(
                            f"line{li} {path + [str(lbl)]}: {exc}")
        walk(m, [])
        # also build the album for this line
        M.Buddy._open_collection(fb)
        for w in root.winfo_children():
            if isinstance(w, tk.Toplevel):
                w.destroy()
        print(f"line {li}: {len(fb.calls)} menu entries fired OK "
              f"({sorted(set(fb.calls))})")
    except Exception as e:
        FAILS.append(f"line{li} build: {e}")
        traceback.print_exc()

# stage variations: Eevee line evolved stages 1..8 menus
for stage in range(1, len(M.STARTER_LINES[M.Buddy.EEVEE_LINE]
                           ["evolutions"])):
    fb = FakeBuddy()
    fb.line_idx = M.Buddy.EEVEE_LINE
    fb.evo_stage = stage
    fb.root = root
    fb._build_menu = M.Buddy._build_menu
    fb._evo_available = lambda evo: M.Buddy._evo_available(fb, evo)
    fb._evo_label = lambda evo: M.Buddy._evo_label(fb, evo)
    fb._evolve_to = lambda s: fb.calls.append(f"evolve{s}")
    try:
        M.Buddy._build_menu(fb)
        print(f"eevee stage {stage} menu builds OK")
    except Exception as e:
        FAILS.append(f"eevee stage {stage}: {e}")

root.destroy()
print()
if FAILS:
    print(f"{len(FAILS)} FAILURES:")
    for f in FAILS:
        print(" ", f)
    sys.exit(1)
print("ALL LINES AND STAGES VERIFIED")
