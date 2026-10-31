#!/usr/bin/env python3
"""parts.py [OUT_DIR]: hide each part of the player ship's model in turn and screenshot the game, to find which part
draws what (for example the window frame seen from the cockpit). Writes OUT_DIR/parts.png (a labelled grid) and
prints each part's name hash (the first dword of its record), as used in tools/build_cockpit_extras.py.

Part records live in the model file (ship*.rcsmodel): +0 name hash, +0x18 name pointer, +0x24 show bits; the scene
draw loop skips a part when bit 1 is clear. Records are found by their name strings (the name follows the record at
+0x48); every copy (LODs, other ships with the model) is toggled. Needs ImageMagick and spectacle."""
import os, struct, subprocess, sys, time
from peek import q, d, rd, wr
from ship import ship
import nodes

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rt')

def shape_names():
    out = []
    def walk(n):
        while n:
            nm = nodes.name(n)
            if nm.endswith('Shape') and nm not in out: out.append(nm)
            walk(q(n + 0x20)); n = q(n + 0x18)
    walk(q(q(ship() + 0x7780) + 0x90))
    return out

def records(names):
    """{name: [record]} for records whose name string (at record+0x48) is one of names."""
    pid = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rt', 'pid')).read().strip()
    want = {n.encode() + b'\0': n for n in names}
    found = {n: [] for n in names}
    for line in open(f'/proc/{pid}/maps'):
        r, perm = line.split()[:2]
        a, e = (int(x, 16) for x in r.split('-'))
        if 'rw' not in perm or not 0x1000000000 <= a < 0x1200000000: continue
        for off in range(a, e, 0x400000):
            try: data = rd(off, min(0x400000, e - off))
            except OSError: continue
            for s, n in want.items():
                i = data.find(s)
                while i != -1:
                    rec = off + i - 0x48
                    if i >= 0x48:
                        try:
                            if q(rec + 0x18) == off + i and d(rec + 0x24) & 7:
                                found[n].append(rec)
                        except OSError: pass
                    i = data.find(s, i + 1)
    return found

def shot(path, label):
    subprocess.run(['spectacle', '-b', '-n', '-f', '-o', os.path.join(OUT, 'full.png')], capture_output=True)
    subprocess.run(['magick', os.path.join(OUT, 'full.png'), '-crop', '2560x1440+1920+0', '+repage', '-resize', '20%',
                    '-gravity', 'north', '-pointsize', '18', '-fill', 'yellow', '-annotate', '+0+30', label, path])

def main():
    names = shape_names()
    recs = records(names)
    tiles = []
    shot(os.path.join(OUT, 'p_base.png'), 'all parts'); tiles.append(os.path.join(OUT, 'p_base.png'))
    for n in names:
        rs = recs[n]
        if not rs: print(f'{n:34} no record'); continue
        h = d(rs[0])
        print(f'{n:34} {h:#010x}  {len(rs)} copies')
        old = [d(r + 0x24) for r in rs]
        for r, f in zip(rs, old): wr(r + 0x24, struct.pack('<I', f & ~1))
        time.sleep(0.35)
        p = os.path.join(OUT, f'p_{n}.png'); shot(p, n); tiles.append(p)
        for r, f in zip(rs, old): wr(r + 0x24, struct.pack('<I', f))
        time.sleep(0.1)
    rows = [tiles[i:i + 4] for i in range(0, len(tiles), 4)]
    rowfiles = []
    for k, row in enumerate(rows):
        f = os.path.join(OUT, f'p_row{k}.png'); subprocess.run(['magick', *row, '+append', f]); rowfiles.append(f)
    subprocess.run(['magick', *rowfiles, '-append', os.path.join(OUT, 'parts.png')])
    print('grid:', os.path.join(OUT, 'parts.png'))

if __name__ == '__main__':
    main()
