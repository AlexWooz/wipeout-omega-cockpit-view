#!/usr/bin/env python3
"""Move the team-ship cockpit eye live, in a terminal next to the game.

  tune_eye.py        (the game must be started with tools/runtime/launch.sh)

Race a team ship in the internal camera, then:
  Left / Right     eye left / right            Up / Down      forward / back
  PgUp / PgDn      up / down                   + / -          bigger / smaller steps
  s                save this ship's eye        r              back to the mod's computed eye
  q                quit

The eye is [ship+0x77e0] (model space: +x left, +y up, +z forward), the offset the mod's loader computes from
the pilot/canopy shape the camera is anchored on ([ship+0x77d0]). Saved eyes go to eye_overrides.json next to
this file, keyed by that shape's name and bounding box, so each ship model has its own entry.
"""
import json, os, struct, sys, termios, tty
from peek import q, b, rd, wr
from ship import ship
import nodes

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE = os.path.join(HERE, 'eye_overrides.json')
STEPS = [0.01, 0.02, 0.05, 0.1, 0.2]
KEYS = {'\x1b[D': (0, +1), '\x1b[C': (0, -1), '\x1b[A': (2, +1), '\x1b[B': (2, -1),
        '\x1b[5~': (1, +1), '\x1b[6~': (1, -1)}

def current():
    """(ship, anchor node, model key, eye) for the player ship, or None when it has no team-ship eye."""
    try:
        s = ship()
        node = q(s + 0x77d0)
    except OSError:                                 # between races: no player ship
        return None
    if not node or b(q(s + 0x6e10) + 0x74d):    # no anchor, or a VR livery (VR_Cam: not ours)
        return None
    box = struct.unpack('<6f', rd(node + 0xdc, 12) + rd(node + 0xec, 12))
    key = nodes.name(node) + ' ' + ','.join(f'{v:.2f}' for v in box)
    return s, node, key, list(struct.unpack('<3f', rd(s + 0x77e0, 12)))

def load():
    try:
        return json.load(open(SAVE))
    except (OSError, ValueError):
        return {}

def read_key():
    k = os.read(0, 1).decode(errors='replace')
    if k == '\x1b':
        k += os.read(0, 2).decode(errors='replace')
        if k[-1] in '56':
            k += os.read(0, 1).decode(errors='replace')
    return k

def main():
    try:
        q(0x800000000)
    except OSError:
        sys.exit('The game is not running, or was not started with tools/runtime/launch.sh.')
    saved = load()
    step = 2
    old = termios.tcgetattr(0)
    tty.setcbreak(0)
    last_ship, computed, msg = None, None, ''
    try:
        while True:
            cur = current()
            if cur is None:
                print('\r\x1b[K no team-ship eye: race a team ship in the internal camera (any key to retry, q quits)', end='', flush=True)
                if read_key() == 'q': break
                continue
            s, node, key, eye = cur
            if s != last_ship:                     # new race: remember what the mod computed
                last_ship, computed = s, list(eye)
                msg = 'saved eye for this ship applied' if key in saved else ''
                if key in saved:
                    eye = saved[key]['eye']; wr(s + 0x77e0, struct.pack('<3f', *eye))
            print(f'\r\x1b[K {nodes.name(node)}  eye x {eye[0]:+.2f}  y {eye[1]:+.2f}  z {eye[2]:+.2f}'
                  f'  step {STEPS[step]:.2f}  {msg}', end='', flush=True)
            k = read_key(); msg = ''
            if k == 'q': break
            if k in KEYS:
                axis, sign = KEYS[k]
                eye[axis] += sign * STEPS[step]
            elif k in '+=': step = min(step + 1, len(STEPS) - 1)
            elif k in '-_': step = max(step - 1, 0)
            elif k == 'r': eye = list(computed); msg = 'back to the computed eye'
            elif k == 's':
                saved[key] = {'eye': [round(v, 3) for v in eye], 'computed': [round(v, 3) for v in computed]}
                json.dump(saved, open(SAVE, 'w'), indent=1, sort_keys=True); msg = f'saved ({len(saved)} ships)'
            wr(s + 0x77e0, struct.pack('<3f', *eye))
    finally:
        termios.tcsetattr(0, termios.TCSADRAIN, old)
        print()

if __name__ == '__main__':
    main()
