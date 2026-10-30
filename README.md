# WipEout Cockpit Camera

A mod for [wipeout_pc](https://github.com/AbdelmoumenDeghbouche/wipeout_pc), the native PC port
of WipEout Omega Collection, that brings the PlayStation VR cockpit view to the normal
flatscreen game.

**Status:** v0.9. The cockpit is drawn in the internal camera (tested in game). Cockpit sounds patched, no audible change yet. In the cockpit view of VR ships the HUD is on the cockpit screens, as in VR; the other cameras and team ships keep the stock HUD. Team ships' internal camera sits at the pilot's eye (or under the canopy) instead of on the bumper. `tools/runtime/` runs and inspects the live game.

## What it does (planned)

Outside VR the game only has chase cameras and a bumper camera. The VR mode adds a camera
locked inside a full 3D cockpit. This mod switches that view on in flatscreen for the ships
that have a cockpit: VR HD, VR Fury, the VR 2048 ships (1-4), and the Zone and Detonator VR
variants. The normal team ships have no cockpit models, so they keep the usual cameras.

## Layout

| Path | What |
|---|---|
| `mod/Cockpit Camera/` | The mod as it goes in wipeout_pc's mods folder (`mod.json`, `patches/*.xml`) |
| `docs/FINDINGS.md` | What the game code does: addresses, struct fields, VR checks |
| `docs/PLAN.md` | Work steps and the test list |
| `tools/eboot_tool.py` | String/xref/disassembly helper for `out/eboot.elf` |
| `tools/psarc_list.py` | Lists the files inside the game's `.psarc` archives |
| `tools/check_patches.py` | Checks each patch signature and site against `out/eboot.elf`, shows the code before/after |
| `tools/build_cockpit_cam.py` | Assembles the team-ship camera code and prints its patch group |
| `tools/runtime/tune_eye.py` | Moves the team-ship cockpit eye live from a terminal and saves it per ship (see below) |
| `tools/psarc_get.py` | Extracts one file from the game's `.psarc` archives |
| `tools/make_signature.py` | Makes a `Pattern`/`At` signature for a patch site |

## Install

Run `./install.sh` (copies the mod to `~/Games/wipeout_pc/mods`), or zip `mod/Cockpit Camera` with
`tools/zip_mod.py` from wipeout_pc. Enable it in the launcher's **Mods** tab together with the
built-in patch **Cheat - VR ships outside VR**, then pick a VR ship and the internal camera.

## Game version

Developed against CUSA07671 (US) 01.00 + update 01.07. The patches use byte signatures
(`Pattern`/`At`) like the port's own, so other builds may work.

No game files are included in this repository. You need your own copy of the game.

## Tuning the cockpit eye

1. Start the game with `tools/runtime/launch.sh` (not the launcher: this lets the tools reach the game's memory).
2. Race a team ship and switch to the internal camera.
3. In a terminal, run `python3 tools/runtime/tune_eye.py`: arrows move the eye left/right and forward/back,
   Page Up/Down up/down, `+`/`-` change the step, `r` resets to the computed eye, `s` saves, `q` quits.

Saved eyes go to `tools/runtime/eye_overrides.json`, one entry per ship model; they are applied again when you race
that ship with the tool running. They are not in the mod yet: they become its per-ship defaults in a later build.
