# EeveeMon

A Gen V animated Pokémon desktop pet for **Windows and macOS**, built as a feature-rich
mod of [BuddyMon](https://github.com/hasturah/buddymon). EeveeMon adds the
**Eevee family** with a real 8-way branching stone evolution system, the
**Torchic → Combusken → Blaziken** line, and an optional AI chat companion
supporting multiple mainstream LLM providers.

The pet lives on your taskbar (or above the Dock on macOS), walks around with gravity physics, and is
entirely controlled from its right-click menu.

![Selection screen](selection_screen.png)

---

## What's new in v1.4

- **Progress persists** — the collection book, the stone inventory,
  your current form/size/shiny and the Gift cooldown are saved to
  `eeveemon_save.json` next to the app. Restart and your pet comes
  straight back — no selection screen, nothing lost. Catching 'em
  all is now a campaign that survives reboots.
- **The pet remembers** — the AI companion keeps the last three
  exchanges and replays them, so the conversation actually continues
  instead of resetting every time.
- Suite grows to 78 checks (save roundtrip, restore path, memory).

## What's new in v1.3

- **Collection book (收集册)** — a 24-card album in the right-click menu:
  locked cards sit face down as `?` with their unlock hint, and every form
  you pick or evolve into flips face-up with its sprite. Catching 'em all
  is now a visible long-term goal.
- **Look Around actually looks** — the screen-capture companion now sends
  a real vision payload to OpenAI (gpt-4o-mini) and Anthropic (Claude
  Haiku), so the pet comments on what is actually on your screen.
  DeepSeek's text-only model keeps an honest in-character fallback, and
  API failures now surface as a visible bubble instead of failing silently.
- **Launcher path bug fixed** — `EeveeMon.bat` no longer hard-codes a
  Python path. It prefers the bundled exe, then any `python` found on
  `PATH`, then the `py` launcher — so double-clicking works on machines
  where Python lives anywhere, or not at all.
- **Menu verified for every Pokémon** — a new walk test exercises every
  enabled entry of every line's right-click menu (all 8 starter lines and
  all 8 Eevee evolution stages). The suite is at 69 checks, all green.

---

## Table of contents

- [What's new in v1.3](#whats-new-in-v13)
- [Features](#features)
- [Quick start](#quick-start)
- [Usage](#usage)
- [AI chat companion](#ai-chat-companion)
- [Testing](#testing)
- [Building from source](#building-from-source)
- [Project architecture](#project-architecture)
- [Related projects](#related-projects)
- [Credits & license](#credits--license)

---

## Features

**Roster** — eight starter cards (4×2 grid) on the selection screen:

| Line | Type | Evolution |
|---|---|---|
| Bulbasaur | Grass | Bulbasaur → Ivysaur → Venusaur |
| Charmander | Fire | Charmander → Charmeleon → Charizard |
| Squirtle | Water | Squirtle → Wartortle → Blastoise |
| **Eevee** | **Multi** | Eevee → any of the 8 Eeveelutions (branching) |
| **Torchic** | Fighting | Torchic → Combusken → Blaziken |
| **Meowth** | Normal | none (single form) |
| **Latias** | Dragon | none (single form) |
| **Pikachu** | Electric | none (single form) |

**Branching evolution** — Eevee's right-click *Evolve* menu offers all eight
Eeveelutions, each with its canonical method displayed and enforced:

| Evolution | Requirement |
|---|---|
| Vaporeon | Water Stone (水之石) |
| Jolteon | Thunder Stone (雷之石) |
| Flareon | Fire Stone (火之石) |
| Leafeon | Leaf Stone (叶之石) |
| Glaceon | Ice Stone (冰之石) |
| Espeon | daytime friendship |
| Umbreon | nighttime friendship |
| Sylveon | fairy bond |

**Real stone economy** — the inventory starts with one stone of each kind;
evolving consumes the stone; the menu shows live counts and disables
`×0` entries. *Gift 进化石* grants a random stone on a 10-minute cooldown.

**Collection book (收集册)** — the right-click *Collection 收集册* menu
opens the card album: all 24 forms face down as `?` cards with their
unlock hint (starter / previous stage / stone name / friendship) until
you choose or evolve into them — collecting the rest of the roster is
the long-term goal. Every form you have ever picked or evolved into
this session flips face-up with its sprite and name.

**Quality of life**

- 1-in-100 shiny chance on spawn, evolution, and reroll
- 4 moves per line with particle effects
- Size presets from 50% to 300%
- Drag to reposition; gravity and wall-bounce physics
- Devolve (Eeveelutions jump straight back to Eevee)
- Magenta-background keyout on the selection screen and an anti-fringe
  edge snap on the taskbar sprite path
- Tk pixmap-budget fix: only starter sprites preload; the rest load lazily
- The launcher bat contains **no hardcoded Python path** — it prefers the
  bundled exe, then any `python` on PATH, then the `py` launcher, so it
  works on machines where Python lives anywhere (or not at all)

## Quick start

### Option A — prebuilt executable (no dependencies)

Download `EeveeMon.exe` from
[Releases](../../releases), double-click, and play. All 48 sprites are
bundled inside the executable.

### Option B — run from source

Windows, Python 3.8+:

```bat
python fetch_sprites.py     REM downloads the sprites into sprites/
python eeveemon.py
```

### Option C — macOS (source run)

The pet is cross-platform: on macOS it uses the window's
`-transparent` attribute with alpha-keyed frames instead of
the Windows colour key, and walks above the Dock. No binary
is provided for macOS (built on Windows) — run from source:

```sh
chmod +x run_mac.sh && ./run_mac.sh
```

or manually: `python3 -m pip install Pillow`,
`python3 fetch_sprites.py`, `python3 eeveemon.py`.

## Usage

Everything is reachable from the pet's right-click menu:

| Action | Menu item |
|---|---|
| Evolve / choose an Eeveelution | Evolve |
| Back to the previous form | Devolve |
| Random stone on a 10-min cooldown | Gift 进化石 |
| Particle-effect moves | Use Move |
| Switch starter line | Change Starter |
| Re-open the animated selection screen (resizable) | 选择界面 (Start Menu) |
| 50% – 300% size | Change Size |
| Re-roll the 1/100 shiny | Reroll Shiny |
| Chat with the pet | Talk to Me |
| Have the pet "look" at your screen | Look Around |
| Open the 24-card collection album | Collection 收集册 |
| Fun bubble animation | Throw Up |
| Exit | Quit |

## AI chat companion

The speech-bubble companion is optional and provider-agnostic. Put two
plain-text files next to the executable (or the script):

`apikey.txt` — one line, your API key:

```
sk-xxxxxxxxxxxxxxxx
```

`provider.txt` — line 1: provider, line 2 (optional): model name:

```
deepseek                    REM default; model: deepseek-chat
openai                      REM model: gpt-4o-mini
anthropic                   REM model: claude-3-5-haiku-latest
```

No files = pure pet mode. The key is read from the local file only, is sent
exclusively to the chosen provider's official endpoint
(`api.deepseek.com` / `api.openai.com` / `api.anthropic.com`), and is never
printed or persisted anywhere else.

**Look Around and vision.** With an OpenAI or Anthropic key, *Look Around*
captures your screen and sends it to the vision-capable model
(gpt-4o-mini / Claude Haiku), and the pet comments on what it sees — in
character. DeepSeek's chat model is text-only, so there the pet honestly
says it cannot see yet; switching the provider file enables real vision.

## Testing

The repository ships a self-contained test suite (no extra framework):

```bat
python test_eeveemon.py       REM 69 checks: sprites, roster, stones,
                              REM evolution, menu walk, carousel, chat,
                              REM collection book, a real API call
python verify_all_menus.py    REM every menu entry of every line and
                              REM every Eevee stage, walked and invoked
```

## Building from source

```bat
build_exe.bat
```

(Windows only — PyInstaller one-file builds are platform-specific.)

This fetches the sprites if missing and produces a one-file
`dist\EeveeMon.exe` via PyInstaller.

## Project architecture

- `eeveemon.py` — the whole application (~1.7k lines), structured as:
  - `STARTER_LINES` — declarative roster: each line carries its
    evolutions (id, name, method, requirement) and moves
  - `Buddy` — the taskbar sprite, physics, right-click menu, and the
    collection book (`unlocked` set + `_open_collection` album)
  - `AgentMind` — the provider-agnostic AI layer (raw HTTP, no SDK);
    `_look_thread` captures the screen and sends vision payloads to
    OpenAI / Anthropic with a text-only fallback for DeepSeek
  - `StarterSelect` — the animated carousel selection screen
  - `load_frames` — GIF loading with a dual transparency strategy:
    magenta bake for the window colour key (taskbar) and alpha keyout
    composited over the card background (selection screen)
- `fetch_sprites.py` — sprite acquisition (Gen V animated GIFs from
  PokeAPI; not stored in this repository)
- `test_eeveemon.py` / `verify_all_menus.py` — the 69-check suite and
  the every-line menu walk
- `EeveeMon.bat` — launcher with no hardcoded Python path (exe →
  `PATH` python → `py` launcher)
- `run_mac.sh` — one-command source run on macOS
- `build_exe.bat` — PyInstaller packaging (Windows)

## Related projects

EeveeMon is one member of a small family of desktop-pet experiments.
They intentionally stay **isolated** (separate folders, separate state)
rather than sharing code; ideas are ported between them as features.

| | EeveeMon | BuddyMon | PokeDesk | IdleMon |
|---|---|---|---|---|
| Stack | Python + Tkinter | Python + Tkinter | C# / .NET 8 WPF | Python + PySide6 |
| Scope | Taskbar pet | Taskbar pet | Full Tamagotchi | Shiny-hunting game |
| Roster | 8 lines incl. the 8-way Eevee branch | 3 Kanto lines | All 151 Gen-1 | Encounters, Gen 1–5 |
| Evolution | Branching + stones (real economy) | Linear 3-stage | Needs/level-based, full life cycle | n/a |
| Extras | Multi-provider AI chat | Optional AI chat | Needs, economy, minigames, weather layer | Encounter counters, collection |
| Status | This project | Upstream (modded here) | Third-party; forked as reference | Third-party; forked as reference |

[BuddyMon](https://github.com/hasturah/buddymon) is the upstream this
project mods. [PokeDesk](https://github.com/Glatzenheikoo/PokeDesk) and
[IdleMon](https://github.com/zainibeats/idlemon) are separate third-party
projects — if you want to archive them, please **fork the originals**
rather than re-uploading their source.

## Credits & license

- Based on [BuddyMon](https://github.com/hasturah/buddymon) (MIT)
- Sprites: [PokeAPI/sprites](https://github.com/PokeAPI/sprites) — Gen V
  Black/White animated sprites, fetched at build time and not stored here
- Pokémon © Nintendo / Game Freak / The Pokémon Company. This is a
  non-commercial fan project, not affiliated with or endorsed by Nintendo.

MIT license — see [LICENSE](LICENSE).
