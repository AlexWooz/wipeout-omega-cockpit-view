#!/usr/bin/env python3
"""Print the player ship model's node tree: name, node address, local position (x, y, z).

Nodes as the game's lookup 0x759200 walks them: root [model+0x90], name [node+0x88]+0x10,
first child +0x20, next sibling +0x18; transform [node+0x78], position at +0x80+0x30."""
import struct
from ship import ship
from peek import q, rd

def name(n):
    p = q(n + 0x88)
    return rd(p + 0x10, 64).split(b'\0')[0].decode(errors='replace') if p else '?'

def pos(n):
    t = q(n + 0x78)
    return struct.unpack('<3f', rd(t + 0x80 + 0x30, 12)) if t else None

def walk(n, depth=0):
    while n:
        p = pos(n)
        print('  ' * depth + f'{name(n)}  {n:#x}' + (f'  ({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})' if p else ''))
        walk(q(n + 0x20), depth + 1)
        n = q(n + 0x18)

if __name__ == '__main__':
    model = q(ship() + 0x7790)
    walk(q(model + 0x90))
