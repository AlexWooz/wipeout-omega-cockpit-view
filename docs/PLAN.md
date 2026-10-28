# Plan

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
