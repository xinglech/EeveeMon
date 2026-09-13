# EeveeMon 🦊🐓

A Gen V animated Pokémon desktop pet for Windows — a mod of
[BuddyMon](https://github.com/hasturah/buddymon) that adds the
**Eevee family** (8-way branching stone evolution) and the
**Torchic → Combusken → Blaziken** line (the rooster 🐓).

The pet lives on your taskbar, walks around with gravity physics,
and everything is controlled by right-clicking the sprite.

## Features

- **5 starter cards**: Bulbasaur / Charmander / Squirtle / **Eevee (Multi)** / **Torchic (Fighting)**
- **Eevee's branching evolution** — right-click Evolve offers all 8:
  Vaporeon (水之石), Jolteon (雷之石), Flareon (火之石), Leafeon (叶之石),
  Glaceon (冰之石), Espeon (白昼亲密度), Umbreon (黑夜亲密度), Sylveon (仙子羁绊)
- **Real stone economy**: inventory starts at ×1 per stone; evolving
  consumes the stone; the menu shows counts and greys out `×0 [已用尽]`;
  "Gift 进化石" grants a random stone with a 10-minute cooldown
- Devolve jumps straight back to Eevee; the other lines use linear 3-stage evolution
- 1-in-100 shiny chance, moves with particle effects, size 50–300%, drag to reposition
- **Optional AI chat bubble** (speech companion) supporting the three mainstream providers:
  `deepseek` (default) / `openai` / `anthropic` — plain HTTP, no SDK
- Magenta-background keyout on the selection screen + edge snap on the taskbar sprite
- Tk pixmap-budget fix: only starter sprites preload; the rest load lazily

## Run it

### Option A — prebuilt exe (friends, zero deps)
Grab `EeveeMon.exe` from [Releases](../../releases). Double-click and play.

### Option B — from source (Python 3.8+, Windows)
```bat
python fetch_sprites.py     :: download the 48 sprites into sprites/
python eeveemon.py
```

### Build the exe yourself
```bat
build_exe.bat               :: pyinstaller --onefile, bundles sprites/
```

## AI chat (optional)

Put two text files next to the exe (or the script):

- `apikey.txt` — one line, your API key (never printed, never committed)
- `provider.txt` — line 1 = provider (`deepseek` / `openai` / `anthropic`),
  line 2 = model name (optional; defaults `deepseek-chat` / `gpt-4o-mini` /
  `claude-3-5-haiku-latest`)

No files = pure pet mode. The key goes only to the official API endpoint
(`api.deepseek.com` / `api.openai.com` / `api.anthropic.com`).

## Credits & license

- Based on [BuddyMon](https://github.com/hasturah/buddymon) (MIT)
- Sprites: [PokeAPI/sprites](https://github.com/PokeAPI/sprites) — Gen V
  Black/White animated sprites, fetched by `fetch_sprites.py` at build time
  (not stored in this repo)
- Pokémon © Nintendo / Game Freak / The Pokémon Company. This is a
  non-commercial fan project, not affiliated with or endorsed by Nintendo.
- MIT license, see [LICENSE](LICENSE).
