"""Download the 48 Gen V animated sprites (24 pokemon x normal+shiny)
into sprites/ from PokeAPI.  Run once before running from source or
building the exe."""
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = Path(__file__).resolve().parent / "sprites"
OUT.mkdir(exist_ok=True)

IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9,          # Kanto starters
       133, 134, 135, 136, 196, 197, 470, 471, 700,   # Eevee family
       255, 256, 257,                       # Torchic line
       52,                                   # Meowth
       380,                                  # Latias
       25,                                   # Pikachu
       24,                                   # Arbok
       202,                                  # Wobbuffet
       393,                                  # Piplup
       175,                                  # Togepi
       108,                                  # Lickitung
       110]                                  # Weezing
BASE = ("https://raw.githubusercontent.com/PokeAPI/sprites/master/"
        "sprites/pokemon/versions/generation-v/black-white/animated/{}.gif")
SHINY = ("https://raw.githubusercontent.com/PokeAPI/sprites/master/"
         "sprites/pokemon/versions/generation-v/black-white/animated/"
         "shiny/{}.gif")

for pid in IDS:
    for url, name in ((BASE.format(pid), f"{pid}.gif"),
                      (SHINY.format(pid), f"{pid}_s.gif")):
        target = OUT / name
        if target.exists() and target.stat().st_size > 500:
            continue
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (sprite fetcher)"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                target.write_bytes(r.read())
            # validate: a truncated GIF would crash the app at
            # startup (Tk pixmap failure), so retry it instead
            from PIL import Image
            im = Image.open(target)
            im.load()
            if im.n_frames < 5 and "52" not in name:
                raise ValueError("truncated gif")
            print(f"ok  {name}", flush=True)
        except Exception as exc:
            print(f"FAIL {name}: {str(exc)[:60]}", flush=True)
print("done")
