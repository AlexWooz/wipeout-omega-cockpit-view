#!/usr/bin/env python3
"""List the files inside the game's .psarc archives (reads only the headers).

  psarc_list.py GAME_DIR [OUT_DIR]   writes <archive>.txt per archive and prints counts
"""
import glob, lzma, os, re, struct, sys, zlib

def manifest(path):
    with open(path, 'rb') as f:
        magic, ver, comp, toclen, esz, n, bs, flags = struct.unpack('>4sI4sIIIII', f.read(32))
        toc = f.read(toclen - 32)
        bsz = 2 if bs <= 0x10000 else 3 if bs <= 0x1000000 else 4
        zl = toc[n * esz:]
        zs = [int.from_bytes(zl[i:i + bsz], 'big') for i in range(0, len(zl), bsz)]
        e = toc[:esz]
        zi = struct.unpack('>I', e[16:20])[0]
        ln = int.from_bytes(e[20:25], 'big'); off = int.from_bytes(e[25:30], 'big')
        f.seek(off); out = b''
        while len(out) < ln:
            z = zs[zi]; zi += 1
            blk = f.read(z if z else bs)
            for dec in (zlib.decompress, lzma.decompress):
                try: out += dec(blk); break
                except Exception: pass
            else: out += blk
    return [s.decode('latin1') for s in re.split(rb'[^\x20-\x7e]+', out) if s]

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    os.makedirs(out_dir, exist_ok=True)
    for p in sorted(glob.glob(os.path.join(sys.argv[1], '*.psarc'))):
        names = manifest(p)
        open(os.path.join(out_dir, os.path.basename(p) + '.txt'), 'w').write('\n'.join(names) + '\n')
        print(os.path.basename(p), len(names), 'files')
