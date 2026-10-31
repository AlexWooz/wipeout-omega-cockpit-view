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

## Team ship cockpit view (in progress, 2026-10-28)

- Team ship models have a pilot and an interior: Feisar HD `FEISAR_PilotShape`, `FEISAR_GlassShape`, `FEISAR_ScreensShape`;
  Qirex HD `PilotShape`, `GlassShape1`, `Windscreen_strip`. No `VR_Cam`/`cockpit` nodes (the loader `0x31d7c0` only looks
  them up for VR liveries anyway). Node tree: `tools/runtime/nodes.py` (root `[model+0x90]`, name `[node+0x88]+0x10`,
  child `+0x20`, sibling `+0x18`, local matrix `[node+0x78]+0x80`, world `[node+0x68]`, dirty bit `0x10` of `+0x61`);
  shape nodes hold a bounding box at `+0xdc` (min) / `+0xec` (max).
- Bounds (ship space, +z forward, +y up): Feisar pilot (-0.48, 0.28, -1.31)-(0.48, 1.44, 1.08); Qirex pilot
  (-0.31, 0.27, -3.71)-(0.31, 1.17, -0.86), glass (-0.38, 0.53, -3.13)-(0.39, 1.45, -0.86). VR HD: VR_Cam (0, 0.52, 0.42)
  under `cockpit` (0, 0.21, 0); pilot (-0.35, -0.38, 0.24)-(0.26, 0.63, 1.4), helmet (-0.11, 0.56, 0.25)-(0.11, 0.84, 0.55).
- Live proof (`tools/runtime/eye.py X Y Z`): an unused node of the model (`persp1`, `pointLight1`) moved to the eye with an
  identity rotation, `[ship+0x77d0]` pointed at it and the view lock `[ship+0x6987] = 2`, then the camera cycled once (the
  model visibility is set on camera change). Qirex HD at (0, 1.05, -3.0): inside the canopy, frame and screen ahead, the
  pilot's arms on the handles in view. With lock 0 the internal camera keeps the bumper position.
- Per-frame visibility: the model `[ship+0x7780]` bit 4 of `+0x60` is cleared every frame by `0x301be5` (camera-change
  visibility, patched by the mod to test `VR_Cam`) and `0x31dfb1` (LOD switch); with the mod and the slot set it stays visible.
- The launcher's `mods.json` may have the mod disabled; `tools/runtime/launch.sh` uses its own mods config with it enabled.

### Camera modes (for a new cockpit mode)

- The race camera is the option list `CameraP1`/`CameraP2` in `data/plugins/frontend/gui/ingame_definition.xml`
  (also `additional_definition.xml`, `ingame_definition_demo.xml`), inside `data00.psarc`:
  `<Entry idstring="OPT_INT|OPT_CLOSE|OPT_FAR">`, default `OPT_CLOSE`. `tools/psarc_get.py` extracts one file
  (TOC entries keyed by the MD5 of the upper-case path).
- `0x2ffd90` sets the camera up from the option string: `OPT_INT` -> `[cam+0x74] = 0` and the ship's internal
  method (vtable `0x97db90` slot `0xf0` = `0x312d80`, sets `[ship+0x6986] = 2`, `+0x6983 = 1`), `OPT_CLOSE`/`OPT_FAR` ->
  1/2 and slot `0xe8` (`0x3129f0`, external). An unknown string changes nothing (`0x300678` jne `0x300ffc`).
  `[cam+0x74] = 3` is set by `0x2fe520` with `[ship+0x6984] = 1` (model hidden; probably the look-back camera).
- Bumper eye: `0x3230d5`, from the camera profile `[[ship+0x6a18]+0xc8]` (Qirex HD: 65, 0, 3.0, 0, 1.3, 5, 1.3, 5;
  probably FOV, height, forward). `InternalCamera`/`BonnetCamera`/... (`0x2f4130`) are not node names in the
  ship `Locators.vex`.
- The port's mods replace whole files; the option list is inside `data00.psarc`, so a new list entry needs either
  a rebuilt archive or a code change that adds the entry in memory.

### v0.8: team ships, internal camera at the pilot's eye (replaces the bumper camera)

Patch group "Cockpit Camera - Team ships", built by `tools/build_cockpit_cam.py` (assembly and notes there):
- New code in `0x301018..0x3015a9`, the VR camera-options block of `0x2ffd90` (runs only with the race VR flag, which
  the port never sets; no branch or pointer leads into it). `0x30100a` now always jumps past it.
- Loader `0x31d8c2` (liveries without a VR cockpit): first shape with a bounding box whose name holds "ilot" (pilot),
  else "lass"/"reen" (canopy glass, windscreen); eye = (mid x, max.y - 0.15, min.z + 0.6) for a pilot,
  (mid x, max.y - 0.45, min.z + 0.5) for glass, stored in `[ship+0x77e0]`; `[ship+0x77d0]` = that node; lock 2.
  Constants (DY, DZ, GY, GZ) at `0x301199` in this build, can be tuned live.
- Camera `0x323081`: team ships add the offset along the node's world axes.
- The VR sound/emitter patches (`0x32f901`, `0x32fc99`, `0x304dac`) now test the VR cockpit node `[ship+0x77d8]`.
- Tested live: Qirex HD (PilotShape: canopy, screen, pilot's arms), Feisar c1 (no pilot, FEISAR_GlassShape:
  windscreen, dash, joystick), VR HD unchanged, 2048 AG-Systems Speed (no pilot/glass names: bumper as before).
- Pilot/canopy shape names in the 69 ship models (`Ship.vex`): PilotShape (23), PIlotShape (8), Pilot_TShape (6),
  Pilot_2048Shape (4), FEISAR_/GOTEKI_/SHIP_/Cockpit_PilotShape, Pilot1/2Shape, Pilot_MeshShape; 13 have none
  (assegai/auricom/feisar `_c1`/`_n1`, mirage, tigron_x, ag_systems2048 1-4); most of those have a glass/windscreen shape.

### 2048 ships (2026-10-28)

- 24 2048 ship models (`ships/<team>2048/1..4`, `ships/VR_2048/1..4`). Pilot shapes: Auricom, Feisar, Qirex `PilotShape`
  (Qirex 3 `Pilot_MeshShape`), Piranha `Pilot1Shape`/`PilotShape`/`Pilot2Shape`, VR_2048 `Pilot_2048Shape`. AG-Systems 1-4
  have none: models 2-4 have `AG_SystemsShape`, a canopy shell with the pilot inside; model 1 has `AG_Systems_GlassShape`.
- The loader now ranks pilot > "msSh" (`AG_SystemsShape`, eye CY/CZ = -0.30/+0.92) > glass/windscreen.
  AG-Systems "Speed" (model 3): `AG_SystemsShape` (-0.63, 0.82, -3.12)-(0.63, 1.45, 0.06), eye (0, 1.15, -2.2), tuned live
  (`tools/runtime/seteye.py`): canopy struts, the lit dash, both arms.
- With the VR ships cheat on, the second unlocked AG-Systems 2048 slot of this save was a VR_2048 ship (VR_Cam, VR cockpit
  and screens HUD): the VR 2048 ships already get the full VR cockpit through the existing patches.

### 2048 HUD with team ships (open, 2026-10-29)

Stock 2048 HUD (mod off): lap "1/4", target time, a plain energy bar bottom right. With the HUD group on, a team ship in
2048 mode shows "LAP"/"TARGET" without values and a team panel with a default "AG SYSTEMS" banner over the energy bar,
in every camera. Live tests (tools/runtime/hudtree.py): moving all of slot 1's elements (the stock-layout HUD, view 0)
off screen removes everything, so those are slot 1's own elements; moving slot 0's off screen changes nothing; swapping
the active HUD (0xa735b0/0xa73680) changes nothing; undoing the whole HUD group gives the stock HUD. So in 2048 the
second HUD the setup makes (r15b = 1) is never filled in: the 2048 HUD values/team go only to the first HUD (slot 0).
HD fills both. Next: find the 2048 HUD update and what limits it to the first HUD (or make the first HUD the screen one).
- Confirmed live: with slot 0 (cockpit HUD, *_VR.xml layout) moved to the screen view it shows the values (1/4, 3.48.52,
  energy bar, at its dash positions), so the 2048 HUD driver (class 0x97d248, `PLAYER HUD`/`PLAYER HUD 1`, resolved by
  name through the registry 0x11ac4c8, not a node of either tree; one object, its +0x10 is stale after a restart) feeds
  only the first HUD the setup makes. Options: skip the VR HUD setup in 2048 mode (team ships stock, VR 2048 ships lose
  the dash-screen HUD), or make the driver feed the screen HUD too (unknown cost).

### 2048 HUD fix (v0.9, tested live 2026-10-29)

The 2048 HUD is filled by driver objects, one per HUD, created by the race managers (time trial 0x5e22a0, and
0x5d75b0, 0x5d96d0, 0x5dd1a0, 0x5e5060, 0x5e8300): only in VR do they create the second driver (constructor arg 1,
name "PLAYER HUD 1", partner link +0x920, stored at [game+0x30100]) and bind each driver's parent to slot[arg]. The
race manager update 0x5cdb30 ticks only [game+0x300f8] (0x5cff83), so even in VR the second driver is never ticked.
v0.9 (tools/build_hud2048.py, in the HUD group): the 9 VR tests take the VR side, and a cave at 0x301500 ticks both
drivers. Checked live: Feisar 2048 Speed time trial shows LAP 4/4, TARGET, TOTAL running and the stock energy bar.
Four sites (0x5d9a20/0x5e53ed, 0x5d7ea8/0x5ddace) are in identical twin functions: address-only lines.
Not checked: other 2048 modes (single race, combat, zone...), VR 2048 ships' cockpit screens with the second driver.

### v0.10: canopy hidden in the team-ship cockpit view (2026-10-29)

The black "struts" seen from the Feisar 2048 cockpit are its `GlassShape` part (the canopy frame) drawn unlit from inside.
2048 models do not use the HD model table (0xedf3e0 entries are empty for them); their parts are records in the model
file `ship*.rcsmodel` (record: +0 name hash, first dword depends only on the name; +0x18 name; +0x24 show bits, 7),
shared by every ship with that model. The main scene draw loop 0x5f2d30 skips a part when bit 1 is clear
(0x5fe80a, 0x5ffb08); clearing bit 1 of the GlassShape record live removed the struts, bits 2/4 did nothing.
v0.10 (tools/build_cockpit_cam.py, Team ships group): both tests call a cave (0x301280) that also skips parts whose name
hash is in GLASS_NAMES (canopy/glass/windscreen parts of all HD and 2048 ship models, collected from the files) while the
player ship is in the internal camera and has a non-VR livery. Every ship with those models loses its canopy then.
Tested live: Feisar 2048 Speed, clean view on the grid and mid-race.

### Team-ship cockpit dropped (v0.11)

The notes on v0.8-v0.10 team-ship camera and canopy hiding describe a removed group. Live finding that ended it: on the
AG-Systems 2048 Speed, hiding `AG_Systems_SPEED_BlackBitsShape` removes the struts but also the arms and dash body.

### v0.12: HUD messages, doubled text, camera mode (checked in game 2026-10-30)

- Each HUD's update (0x26b030, 0x27787e) reads and clears the message flags [[hud+0x78]+0x138], so the cockpit HUD took
  every message: centred on regular ships (its Info1 at 255,255 on view 0), nothing on VR ships in third person (hidden).
  Cave 0x301480: the cockpit HUD takes them only when the screen HUD is hidden, and hides itself when the screen HUD shows,
  which also ends doubled text such as WRONG WAY on regular ships. Built by tools/build_hud2048.py.
- View lock [ship+0x6987]: 0 track (camera fixed to the track, ship rotates), 1 pilot (camera rotates with the ship),
  2 cockpit (gimballed). The mod defaults to 1 (0x32f7f7, 0x3358b6); since v0.15 the menu option decides.

### v0.13: Zone ships (checked in game 2026-10-30)
- Zone race manager `0x2ca3f0` picks the team with `cmp byte [VR],0` at `0x2ca89f`: `vr_zone` with the flag, otherwise `zone` (no cockpit). Patched to always take `vr_zone`.
- Zone HUD update: `[hud+0xa60]`/`[hud+0xa68]` are the next-tier row (`0xa68` is the text, set by `0x280bc5`). At `0x273bc7` the row is left hidden only with the VR flag and `[0xa73680] == [0xa73690]`. Without the flag it drew flat over the cockpit view. Patched to the VR side; the third-person row still shows.
- Element view byte `+0xf8`: the dash elements use 1. Setting another element's byte to 1 takes it off the screen.
- Detonator shows the cockpit view with no patch of its own (checked in game). Its manager `0x2ba160` has a VR check at `0x2bb242`, left as it is.

### v0.14: window frame hidden in the VR cockpits (checked in game 2026-10-30)
The dark struts are the ship's `Window_glassShape` part, present in all nine VR models with one name hash (`0x0f4c410b`). Hidden live on 2048 VR model 3: struts gone, dash and hull intact.
Built by `tools/build_window.py`: the draw loop tests (`0x5fe80a`, `0x5ffb08`) call a cave at `0x301280` that also skips this part while the player ship is in the internal camera and has a cockpit. Other ships with the same model lose the part during that time too.

### v0.15: VR camera option in Game Options (checked in game 2026-10-30)
"Camera settings - VR" (setting `CameraVR`, values `OPT_INT_LOCKED_COCKPIT`/`TRACK`/`PILOT`) was greyed out without the front-end VR flag. `0x596034` now always takes the enabled side. The code applying it to `[ship+0x6987]` is in the never-run block of `0x2ffd90`, so the camera update hook at `0x30100a` jumps to a new cave at `0x301300` that does the same for ships with a cockpit. All three modes work, the choice saves, and no warning appeared. The default in a save without a choice is Cockpit. Built by `tools/build_window.py`.

### Tools removed in the cleanup
`tools/build_cockpit_cam.py` and `tools/runtime/{tune_eye,eye,seteye,hud}.py` are no longer in `tools/`; notes above that name them refer to commit `06c12b4` and earlier. `tools/build_window.py` is now `tools/build_cockpit_extras.py`.
