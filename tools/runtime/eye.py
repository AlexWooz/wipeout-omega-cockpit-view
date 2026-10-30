#!/usr/bin/env python3
"""eye.py X Y Z: put the player ship's internal camera eye at (X, Y, Z) in ship space, live.
Moves an unused node of the model (Maya camera persp1, or pointLight1/top1) there with an identity rotation (it then faces the ship's way),
points the ship's VR_Cam slot [ship+0x77d0] at it and sets the view lock [ship+0x6987] to 2, as VR ships
have it: with lock 0 the internal camera takes the bumper position instead."""
import sys, struct
from ship import ship
from peek import q, b, rd, wr
import nodes

def find(n, want):
    while n:
        if nodes.name(n) == want: return n
        r = find(q(n + 0x20), want)
        if r: return r
        n = q(n + 0x18)

s = ship()
root = q(q(s + 0x7790) + 0x90)
node = next(n for n in (find(root, nm) for nm in ('persp1', 'pointLight1', 'top1')) if n)
x, y, z = (float(v) for v in sys.argv[1:4])
t = q(node + 0x78)
wr(t + 0x80, struct.pack('<16f', 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1))
wr(node + 0x61, bytes([b(node + 0x61) | 0x10]))
wr(s + 0x6987, b'\x02')
wr(s + 0x77d0, struct.pack('<Q', node))
print('eye node', hex(node), 'local', struct.unpack('<3f', rd(t + 0xb0, 12)))  # its world matrix [node+0x68] is built on the next update
