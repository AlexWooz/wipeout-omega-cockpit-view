# Findings

All addresses are game virtual addresses in `out/eboot.elf` (US 01.07). In the patch XML
`Address` attribute they are **+0x400000** (for example 0x322fd0 -> 0x722fd0).

## Assets

Only the VR ships ship a cockpit interior (textures `*_Cockpit_DS/N.gnf`, cockpit nodes in the model):

- `data/art/published/HDShips/VR_HD`, `VR_FURY`, `VR_FURY_n1`
- `data/art/published/ships/VR_2048/1..4` (textures in `ships/common_textures`)
- `data/art/published/HDShips/Zone_VR`, `Detonator_VR`

Regular team ships (`hdships/ag_systems`, `ships/feisar2048`, ...) have no cockpit models.
Cockpit-only weapon effects: `Data/weapons*/vr_shield_cockpit`, `vr_absorbinternal_cockpit`,
`vr_leechbeamdamage_cockpit`. VR HUD: `data/HUD/vr_*.vex`.

## Flags and globals

| Where | Meaning |
|---|---|
| `0x1047e20` bit 0 | VR mode (front end) |
| `0x1012810` (byte) | VR mode for the current race; copied from 0x1047e20 at `0x5ab99b`. About 155 reads, so it cannot simply be forced on |
| `0x9a78ec` (float) | "Ship Effects VR.Internal Camera Scale" (ship scale in VR internal view) |

## Ship struct fields

| Field | Meaning |
|---|---|
| `+0x6e10` -> `+0x74d` | Livery/team is a VR ship (same flag as the "VR ships outside VR" cheat) |
| `+0x6983` | Internal camera active |
| `+0x6984` | (also hides the model; set by look-back / camera switching, to check) |
| `+0x6986` | Camera mode: 1 external, 2 internal (set at 0x312a06 / 0x312d8c) |
| `+0x6987` | VR view lock: 0 track, 1 pilot, 2 cockpit. Default 2 (0x32f7f1, 0x3358b0); reset to 0 at 0x31d906 if the ship has no cockpit |
| `+0x7600` | Ship scale (replaced by 0x9a78ec in VR internal view) |
| `+0x7780` | Ship model instance; bit 0x4 of `[model+0x60]` = visible |
| `+0x7790` | Ship model resource (node lookups) |
| `+0x77d0` | `VR_Cam` node (camera locator), null on non-VR ships |
| `+0x77d8` | `cockpit` node |
| `+0x77e0` | cockpit node transform (copied at load) |
| `+0x77f0/+0x77f8` | `Window_shieldShape` (canopy) mesh index |

## Functions

| Address | What | VR check |
|---|---|---|
| `0x31d7c0` | Finds `VR_Cam`, `cockpit`, `Window_shieldShape` in the ship model when `+0x74d` is set | none (works outside VR) |
| `0x322fd0` | Internal camera eye. If `+0x77d0` is set, eye = VR_Cam position; if `+0x6987 != 0`, orientation from the node too. Otherwise bumper position, lean and jolt | none |
| `0x31df70` (`0x31e076`..`0x31e092`) | Model visibility at setup: internal camera hides the ship unless VR and VR_Cam | `0x31e07f` |
| `0x31e45a` | Same, second path | `0x31e463` |
| `0x301bb0` | Visibility when the camera changes | `0x301bc7` |
| `0x304ab0` (`0x30649c`) | Uses 0x9a78ec as ship scale when VR_Cam + internal | none |
| `0x306758`, `0x33a2c7` | Extra work on the VR_Cam matrix (probably the head pose) | yes |
| `0x32f8f0` | Creates the cockpit sound emitters (engines, servos, speed meter, consoles, chassis; these are sound names, not the screens) and attaches each to a matrix at ship+0x6080..0x6340 | `0x32f901` |
| `0x32fc90` | Starts the cockpit loops on those emitters, sound group `VR_Ship_HD` / `_FURY` / `_2048` (in the normal ship banks) | `0x32fc99` |
| `0x304dac` (in ship update `0x304ab0`) | Player ship: calls `0x324160`, which writes the cockpit part matrices the emitters follow, and sets the audio listener `0x11aaa78` to ship+0x6200 (otherwise a fixed default pose). Without it the loops have no position | yes |
| `0x333bd1`, `0x338ee2` | Player ship engine sound: in VR the `Ship_NGP_VR_High/Main` events on the cockpit exhaust emitters, otherwise the normal engine on ship+0x5f70 | yes (not patched) |
| `0x7b1c68` (second ship update copy `0x7b1850`) | Same call to `0x324160`, but behind another flag `0x1212d2b` (set from an import at 0x7fa5dc) | not patched |
| `0x31cd16` | Ship LOD choice; VR keeps a higher LOD | `0x31cd1f` |
| `0x2ffd90` | Debug camera/options setup: `OPT_INT/CLOSE/FAR`, `VR_1_INTERNAL` ..., `OPT_INT_LOCKED_*` | |
| `0x329e60` | Cockpit node update when lock = cockpit | none |

### Cockpit screens

The VR ship liveries carry `hud_render_target.gnf`. The ship loader (`0x31dbbd`, no VR check) binds that
texture name to `0x103f3e8`, the texture of render target `0x103f420` (made at renderer init, 0x644c76).

| Address | What | VR check |
|---|---|---|
| `0x284a40` | HUD setup. VR branch (`0x284c4b`): layout `*_VR.xml` / `*_VR_Ext.xml`, model `data/HUD/vr_*.vex` in `0xa735c8`, HUD object in slot `0xa73690[n]` | `0x284c4b` |
| `0x27a130` | HUD virtual: if the HUD is in a VR slot, sets `[frame(0x104abf8)+0x33611] = 1` (render to texture) | via the slots |
| `0x66660e` | Pass that draws into `0x103f420` when `[frame+0x33611]` is set: clears it, then draws view list `frame+0x333b0` (current pointer `0x104aab8`, set up in `0x6689f0`) | |

Taking only the VR branch of the HUD setup is not enough (tested v0.3): the flat HUD stops drawing, the texture is cleared but stays empty and the `vr_hud` frame is drawn over the view. The missing piece: the HUD setup writes the HUD's view `[hud+0xd88] = VR * 2` (`0x285d82`). The HUD code copies it to each element's `[elem+0xf8]`, and elements draw into view list `[0x104aad0 + view*8]` (0 = screen, 2 = HUD texture).

HUD-area VR checks by function (from a sweep of 0x25c000-0x2e0000): `0x26b030` (14, in-race HUD update, target reticule), `0x2d3c50` (7, HUD values/text), `0x27c860` (3), `0x2d1590` (1, `PLAYER HUD`), `0x269b40` (1, picks slot `0xa73690[n]` in VR, else `0xa735b0`), plus the race managers' HUD XML choices.

The port's existing patch file already touches 0x322fd0 (camera lean and jolt above 60 FPS),
so patches there must stay compatible with those.

## Runtime (tools/runtime)

`tools/runtime/launch.sh` starts the game like the launcher (same patches as the saved settings) through a
stand-in `gamemoderun` that keeps the game as its child, so its memory can be read and written under
`ptrace_scope` 1 (`peek.py`: `G(addr)` for eboot statics, which live at host `0x800000000 + addr`; heap
pointers are host addresses). Input goes through `out/pad` (`tools/press.sh` of the port). Screenshots: `spectacle -b -n -f`.

Seen with the v0.4 patches, Racebox single race, internal camera:

- Two HUD objects, as in VR: slot 0 `0xa73690` (layout `*_VR.xml`, cockpit) and slot 1 `0xa73698`
  (`*_VR_Ext.xml`, external views). The camera switch (`0x3129f0`, `0x312e8f`) makes slot 0 the active HUD
  (`0xa735b0`, `0xa73680`, `[hud+0x26a]=1`, visible bit 4 of `[hud+0x60]`) and hides slot 1. Only the slot 1 HUD
  draws the `vr_hud` visor model (`0x27a130`).
- HUD elements (vtable `0x984268`, 112 of them referenced from the HUD object) carry the view in `[elem+0xf8]`;
  the HUD's `[hud+0xd88]` is copied into them only when they are set up, not every frame.
- View lists per frame (`0x669486`): view 0 `frame+0x33150` (screen), view 1 `frame+0x333b0` (drawn into the HUD
  render target by `0x66660e`), view 2 `frame+0x334e0` (screen, drawn before view 0 at `0x66b381`), view 3 `frame+0x33280`.
  `0x279e50` (HUD virtual) points view 0 and view 2 at null when `[hud+0x269]` is 0. List header: `+0x38` viewport w/h, `+0x3c` item count.
- Elements on view 0: drawn on screen in the VR layout. On view 2: not drawn with the race VR flag off, drawn on
  screen with it on. On view 1: they reach the list (count +192) but nothing shows on the cockpit screens.
- The ship model's meshes (`[ship+0x7790]` -> `0xedf3e0[+0x3f38*0x360 + 0x118]` -> `+0x40`, count `+0x38`), show flag `[mesh+0x24]` (7 shown, 0 hidden):
  `HUD_ArcadeShape` (11) shown, `HUD_ElimShape` hidden, `Window_shieldShape` hidden, `Window_mask_small/large` hidden, `Pilot_HelmetShape` hidden.

### Why the screens stayed empty, and the fix

The HUD render target `0x103f420` is created 1x1 at renderer init (`0x7e8990(obj, 5, fmt, 1, 1, 1)` near
`0x644bcb`) and resized only by the display setup `0x64b470` (runs when the display mode `0x103ed1c` changes,
for example when a race starts). Its size: 960x540 times (2 when mode `0x101280c` is 6 and `0x10129e8` is 1), but 1x1
unless the front end VR flag `0x1047e20` is set and the setup's mode argument is 2-4 (`0x64b5a2`-`0x64b5d0`).
With both `cmove ..., esi` gone it is always full size (seen 1280x720 live in a race), and the HUD shows on
`HUD_ArcadeShape` (the dash screens, ship mesh 11) and in the `vr_hud` visor frame.

Tested live (v0.5, Racebox time trial, VR HD livery): dash screens show lap, record, shield, speed and race
time; no flat HUD. Third person (triangle switches camera): the visor frame shows the external VR HUD.

### Team ships (solved in v0.6, kept for the record)

With a non-VR livery (`[livery+0x74d]` 0, no `VR_Cam`) the camera switch never swaps the two VR HUDs
(`0x312a1d` tests the livery), so both stay visible and the HUD is drawn twice. The VR HUD setup has to happen
only for VR liveries, but the HUD is set up about 25 ms before the player ship exists (polled live), so the
choice must come from the front end's selection. Found so far: the livery object is referenced from a
heap record (`... 1, obj, livery ...`) with no static pointer to it; `0x10128d0` is the chrome livery flag, not this.

### v0.6: stock HUD in the external cameras, no sway on the screens

- The HUD setup makes the external HUD by calling itself with r15b set (`0x284c6c`); that path renames the
  layout to `*_VR_Ext.xml`. v0.6 skips the rename (stock layout) and presets `[hud+0xd88] = 2`; the view line at
  `0x285d82` is now `xor byte [rbx+0xd88],2`, so the cockpit HUD gets view 2 and the external one view 0 (screen).
  The visor model (drawn for the external HUD at `0x27a18e`) is skipped.
- HUD sway: the HUD node `[hud+0x948]` (class `0x98b2a0`, parent of the HUD elements; absolute position =
  parent + local `+0x74`, `0x3fd470`) gets a local offset from the ship's movement at `0x26eeda`; the VR test at
  `0x26ede4` skips it in VR. v0.6 tests `[hud+0xd88] & 2` there instead: no sway on the cockpit HUD, stock sway on the external one.
- Team ships: the camera switch never swaps the HUDs for them, the external (stock) HUD shows in every camera
  and the cockpit HUD draws only into view 1/2, so they look stock. Checked live in third person and bumper camera.

### v0.7: no tilt on the cockpit HUD

With the VR flag set live the shield/weapon hexagon on the cockpit screens is level; flipping the HUD update's
VR checks to their VR side one group at a time (live, in memory) narrowed it to `0x26e6b5`: outside VR, bit 1 of
`[node+0x158]` of the HUD node `[hud+0x948]` is set from `[ship+0x6985]` (1 in the cockpit camera), which tilts
the HUD. The block now tests the HUD's view; `al` keeps the view for the next test, of `[hud+0x950]`, a node both
HUDs share (the external stock HUD keeps setting its bit).
