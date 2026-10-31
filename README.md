# WipEout Cockpit Camera

A mod for [wipeout_pc](https://github.com/AbdelmoumenDeghbouche/wipeout_pc), the native PC port
of WipEout Omega Collection, that brings the PlayStation VR cockpit view to the normal
flatscreen game.

**Status:** complete at v0.15.

## What it does

Outside VR the game only has chase cameras and a bumper camera. VR mode adds a camera inside a
full 3D cockpit. This mod turns that view on in the flatscreen game for the ships that have a
cockpit: the VR HD and VR 2048 ships, and the Zone and Detonator VR ships. Regular team ships
have no cockpit models, so they keep the stock bumper camera.

On a VR ship:

- **Cockpit view:** the internal camera puts you in the cockpit.
- **HUD on the dash:** in the cockpit view the HUD is on the cockpit screens, with no flat HUD.
  Third person keeps the stock HUD.
- **Clear window:** the window frame is hidden in the cockpit view.
- **Camera modes:** **Camera Settings - VR** in Game Options is enabled and saved:
  - **Lock camera to cockpit:** the game's default for this option, gimballed.
  - **Lock camera to track:** the camera stays level with the track and the ship rotates.
  - **Lock camera to pilot:** the camera rotates with the ship.
- **Zone:** Zone races use the VR Zone ships.

It also fixes the 2048 HUD on all ships: the lap, time and team readouts, perfect-lap and
final-lap text, and doubled text such as "Wrong way".

## Known limits

- Split screen is untested.
- Other ships using your VR model also lose their window frame while you are in the cockpit view.
- Cockpit sounds are patched, but no audible change was heard in testing.

## Install

Run `./install.sh` (copies the mod to `~/Games/wipeout_pc/mods`), or zip `mod/Cockpit Camera` with
`tools/zip_mod.py` from wipeout_pc. Enable it in the launcher's **Mods** tab together with the
built-in patch **Cheat - VR ships outside VR**, then pick a VR ship and the internal camera.

## Game version

Developed against CUSA07671 (US) 01.00 + update 01.07. The patches use byte signatures
(`Pattern`/`At`) like the port's own, so other builds may work.

No game files are included in this repository. You need your own copy of the game.

## Layout

| Path | What |
|---|---|
| `mod/Cockpit Camera/` | The mod as it goes in wipeout_pc's mods folder (`mod.json`, `patches/*.xml`) |
| `docs/FINDINGS.md` | What the game code does: addresses, struct fields, VR checks |
| `docs/PLAN.md` | Work log and decisions |
| `tools/build_hud2048.py` | Generates the 2048 HUD and HUD message lines of the mod |
| `tools/build_cockpit_extras.py` | Generates the window frame and VR camera option lines of the mod |
| `tools/check_patches.py` | Checks each patch signature and site against `out/eboot.elf`, shows the code before/after |
| `tools/make_signature.py` | Makes a `Pattern`/`At` signature for a patch site |
| `tools/eboot_tool.py` | String/xref/disassembly helper for `out/eboot.elf` |
| `tools/psarc_list.py`, `tools/psarc_get.py` | List and extract files in the game's `.psarc` archives |
| `tools/runtime/` | Runs the game with memory access (`launch.sh`) and inspects it live (`peek.py`, `hudtree.py`, `nodes.py`, `parts.py`, ...) |

The build tools need `keystone-engine` and `capstone`.
