#!/usr/bin/env python3
"""Extract one file from the game's .psarc archives.

  psarc_get.py GAME_DIR PATH OUT_FILE   PATH as psarc_list.py prints it (case-insensitive)
"""
import glob, hashlib, lzma, os, struct, sys, zlib
from psarc_list import manifest

def read_entry(f, toc, esz, zs, bs, k):
    e = toc[k * esz:(k + 1) * esz]
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
    return out[:ln]

def get(path, want):
    name = next((n for n in manifest(path) if n.lower() == want.lower()), None)
    if name is None: return None
    md5 = hashlib.md5(name.upper().encode('latin1')).digest()   # of the upper-case path
    with open(path, 'rb') as f:
        magic, ver, comp, toclen, esz, n, bs, flags = struct.unpack('>4sI4sIIIII', f.read(32))
        toc = f.read(toclen - 32)
        bsz = 2 if bs <= 0x10000 else 3 if bs <= 0x1000000 else 4
        zl = toc[n * esz:]
        zs = [int.from_bytes(zl[i:i + bsz], 'big') for i in range(0, len(zl), bsz)]
        # entries start with the MD5 of their path (not in manifest order)
        k = next(i for i in range(n) if toc[i * esz:i * esz + 16] == md5)
        return read_entry(f, toc, esz, zs, bs, k)

if __name__ == '__main__':
    if len(sys.argv) != 4: sys.exit(__doc__)
    for p in sorted(glob.glob(os.path.join(sys.argv[1], '*.psarc'))):
        data = get(p, sys.argv[2])
        if data is not None:
            open(sys.argv[3], 'wb').write(data); print(os.path.basename(p), len(data), 'bytes'); break
    else: sys.exit('not found')
