#!/usr/bin/env python3
"""hudtree.py [SLOT VIEW]: list the GUI tree under HUD slot 0/1 (0xa73690/0xa73698): counts by vtable and view
byte +0xf8; with SLOT VIEW, set +0xf8 of every node in that tree to VIEW."""
import sys, collections
from peek import q, b, wr, G

def tree(o, out, depth=0):
    c = q(o + 0x20)
    while c and len(out) < 5000:
        out.append(c); tree(c, out, depth + 1); c = q(c + 0x18)
    return out

for slot in (0, 1):
    h = q(G(0xa73690 + 8 * slot)); nodes = tree(h, [])
    print('slot', slot, hex(h), len(nodes), 'nodes', dict(collections.Counter((hex(q(n)), b(n + 0xf8)) for n in nodes).most_common(8)))
    if len(sys.argv) == 3 and int(sys.argv[1]) == slot:
        for n in nodes: wr(n + 0xf8, bytes([int(sys.argv[2])]))
        print('  set view', sys.argv[2])
