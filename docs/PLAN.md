# Plan

**Status: complete at v0.17 (2026-10-31).** This file is the work log. The team-ship camera, eye tuner and canopy hiding
sections are history: that feature was dropped in v0.11 and its tools (`build_cockpit_cam.py`, `tune_eye.py`, `eye.py`,
`seteye.py`) were removed from `tools/` later. They are in git up to commit `06c12b4`.

## 0. No-patch check
Enable **Cheat - VR ships outside VR**, pick VR HD, switch to the internal camera.
Expected: the camera sits at the cockpit eye point but the cockpit is not drawn.
This proves the `VR_Cam` path in 0x322fd0 works outside VR.

## 1. Draw the cockpit
Patch the three visibility checks (0x31e07f, 0x31e463, 0x301bc7) so a ship with a `VR_Cam`
node stays visible in the internal camera even without VR.
Check: near-plane clipping, canopy glass, LOD (0x31cd1f), shadows and lighting.

## 2. Instruments and sound
Patch 0x32f901 and 0x32fc99 (emitters and loops) and 0x304dac (per-frame emitter positions) so the cockpit ambience plays.
v0.1 test: cockpit drawn, third person fine, but no cockpit sounds (0x304dac was missing) and the console screens stay dark.
v0.2 test: no crash; no audible difference between cockpit and third person. Sound is low priority for now (2026-10-27).
Next if needed: the VR engine sound (0x333bd1, 0x338ee2). The screens show the HUD render target; it is only drawn for HUDs set up by the VR branch of the HUD setup (see FINDINGS).
v0.3 test of the experimental patch (always take that branch): no crash, but the flat HUD is gone, the screens only turn light grey (the texture pass runs and clears) and in third person the vr_hud frame is drawn over the view with nothing in it. The HUD items are not sent to the texture view: that choice is made in the HUD draw code (many VR checks, 0x26xxxx-0x2dxxxx). The texture view is draw list frame+0x333b0, current pointer 0x104aab8, viewport set in 0x6689f0. Patch now off by default.
v0.4: also force the HUD view to 2 (0x285d82); the patch group is on again as "VR HUD (experimental)". Still for every ship. Next: limit it to ships with a cockpit, then check the visor frame in third person, the reticule and the other VR checks in 0x26b030.
Check: they move with speed and steering, no crash on load, restart or quit.

## 3. Polish
- Field of view (VR used the headset's)
- Ship scale 0x9a78ec in internal view
- Cockpit shield and weapon hit effects
- HUD over the cockpit
- Camera shake and the port's 60+ FPS camera patches
- Look-back camera

## 4. Optional
- VR 2048 ships outside VR (the existing cheat names only VR HD and VR Fury)
- Team handling on a VR ship by swapping `handlingstats.xml` (plain file mod)

## Test list
- [ ] HD race, Fury race, 2048 race
- [ ] Zone (Zone_VR), Detonator (Detonator_VR)
- [ ] Time trial with ghost
- [ ] Respawn, elimination, ship destroyed
- [ ] 60 FPS and 144+ FPS
- [ ] DLSS / FSR on and off (smearing on the static cockpit)
- [ ] Split screen
- [ ] Mod disabled: game behaves as stock

## VR HUD status (2026-10-27)
- [x] HUD on the cockpit screens and in the visor frame (v0.5: HUD render target sized outside VR)
- [x] Team ships keep the stock HUD (v0.6)
- [x] Stock HUD in the external cameras of VR ships (v0.6)
- [x] No sway on the cockpit screens (v0.6)
- [x] No tilt of the hexagon on the cockpit screens (v0.7)
- [ ] Check race with weapons (target reticule), elimination, zone, 2048 ships, split screen

## Port compatibility
- 2026-10-27, wipeout_pc fd952eb (launcher 0.2.40): all 14 patches applied (patch_status, no skips) and in memory;
  cockpit screens, no sway/tilt, stock HUD in third person checked live. The resolution patches write the HUD
  render target size constants next to the 0x64b5bf/0x64b5d0 sites; the port matches signatures against the
  unpatched eboot, so they do not interfere.

## Next: cockpit view for team ships (planned 2026-10-27, not started)

Goal: an internal camera in the pilot's seat of the regular team ships (no tailor-made cockpit), with the stock HUD
as in third person; if the models allow it, the inside of the ship and the pilot (arms) in view.

What is known:
- Team ships (`hdships/<team>`, `_c1`, `_n1`, `ships/<team>2048`) ship `Ship.vex`/`ship.rcsmodel`, `Locators.vex` and a
  canopy glass texture (`*_Glass_Diffuse.gnf`), but no pilot or cockpit textures: the pilot is probably not modelled,
  or only painted on the canopy.
- VR ships have `PilotShape` (shown) and `Pilot_HelmetShape` (hidden in the cockpit view); `VR_Cam` sits at the eye.
- The internal camera (`0x322fd0`) uses `VR_Cam` when the ship has it, else the bumper position; the ship model is
  hidden in the internal camera unless `VR_Cam` is set (`0x31e07f`, `0x31e463`, `0x301bc7`, now keyed on `VR_Cam`).
- Team ships already get the stock HUD in every camera (v0.6), so the HUD needs no work.

Steps (step 1 and 2 done for Feisar HD and Qirex HD, see FINDINGS "Team ship cockpit view"):
1. List a team ship's meshes and nodes live (`tools/runtime`, `ship.py` mesh listing; nodes via the model resource
   `[ship+0x7790]`): look for a pilot, seat, canopy or camera locator. Also read `Locators.vex` node names.
2. Pick an eye point: a locator if one fits, else a fixed offset from the ship origin per ship class (HD, Fury, 2048),
   tuned live by writing the camera position (`0x322fd0` output) from `peek.py`.
3. Camera: give team ships an internal camera at that point. Either a third camera mode, or replace the bumper camera
   (decide with the user). Options: point `[ship+0x77d0]` at a locator node (the VR path then does the rest; check
   everything else keyed on `0x77d0` — cockpit sounds, HUD swap, emitters — and keep those off for team ships), or
   patch the bumper offset in `0x322fd0`.
4. Model visibility: show the ship model in that camera (the three checks above) and see what the inside looks like:
   backfaces, near-plane clipping, the canopy glass from inside, engine flare and shield effects drawn around the camera.
5. Pilot (VR ships first): check whether `PilotShape` has arms that are visible from `VR_Cam`, and whether moving the
   eye or showing `Pilot_HelmetShape` helps. For team ships only if step 1 finds a pilot mesh.
6. Checks: all team ships and the 2048 ships, look-back camera, ship destroyed/respawn, 60 and 120+ FPS, weapons
   effects (shield, absorb, leech beam have `_cockpit` variants only for VR ships).

Decisions (user, 2026-10-27):
- A new camera mode if possible; if that cannot be done, change the bumper camera instead. For step 3, first find how
  the camera modes are cycled (triangle; `[ship+0x6986]` 1 external / 2 internal, `0x3129f0`) and whether a mode can be added.
- Broken or empty insides are handled while testing: per ship, hide the meshes that get in the way (the `[mesh+0x24]`
  show flag, as `0x3129f0` does for the VR cockpit meshes) rather than falling back to the bumper camera up front.

## Team ship cockpit camera status (2026-10-28)
- [x] Internal camera at the pilot's eye for team ships (v0.8, replaces the bumper camera; decision: user)
- [ ] Tune the eye per ship family if needed; check more ships (Goteki, Piranha, Tigron, Auricom, Assegai, Mirage, Fury ships)
- [ ] 2048 ships without pilot/glass shape names keep the bumper camera (e.g. AG-Systems Speed: canopy is `AG_SystemsShape`)
- [ ] Look-back, respawn, weapons effects, split screen in the new view
- [ ] Later, maybe: a separate camera mode instead (needs a new `CameraP1` list entry, see FINDINGS "Camera modes")

## 2048 ships status (paused 2026-10-28)
- [x] AG-Systems 2048 Speed: `AG_SystemsShape` canopy, eye (0, 1.15, -2.2) — tested live
- [x] Feisar 2048 Speed: `PilotShape` (only nodes named "...Shape" are taken now; the group node `Pilot` gave a bad eye) — tested live
- [ ] Qirex, Piranha, Auricom 2048 (most locked on this save), AG-Systems 1 (`AG_Systems_GlassShape`)
- VR_2048 liveries get the full VR cockpit already

## Live eye tuner (decided 2026-10-28, tool written 2026-10-29: tools/runtime/tune_eye.py)
- `tools/runtime/tune_eye.py`: terminal tool, game started with `tools/runtime/launch.sh`; arrows / PgUp-PgDn move the
  team-ship eye `[ship+0x77e0]` live, shows the values, a key saves them per ship model (pilot/canopy shape name + bounds).
- Saved values become a per-ship override table in `tools/build_cockpit_cam.py` (falls back to the bounding-box rule).
- In-game controls (button + D-pad) only if wanted later.

## Canopy struts per ship (paused 2026-10-29)
- [x] Feisar 2048 Speed: `GlassShape` hidden in the cockpit view (v0.10, uncommitted)
- [x] Third person keeps the canopy; VR 2048 unchanged (checked by the user)
- [ ] Struts still show on AG-Systems 2048, a Qirex ship and Feisar HD: their frames are other parts. Next: in each
      cockpit view (race running, on the grid, controller untouched) run `tools/runtime/parts.py`, read the grid,
      and add the strut parts' name hashes to GLASS_NAMES in tools/build_cockpit_cam.py, then rebuild (--write).
- [ ] Eyes not tuned yet for these ships

## Decision 2026-10-30: no cockpit view for team ships
v0.11 removes the "Team ships" group: team ships keep the stock bumper camera; the cockpit view is VR ships only.
Reason: on some ships the struts can't be hidden alone (AG-Systems 2048 Speed: struts, arms and dash body are one mesh,
`AG_Systems_SPEED_BlackBitsShape`), and the user wants all ships or none. The sections above about team ships, the eye
tuner and canopy hiding are history; the builder and tools stay in tools/ for reference.
