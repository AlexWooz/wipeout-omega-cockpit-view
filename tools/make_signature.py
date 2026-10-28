#!/usr/bin/env python3
"""Make a Pattern/At signature for a patch site in out/eboot.elf.

  make_signature.py ELF START END SITE
START..END: instruction-aligned range of game addresses to sign; SITE: the patched address.
Rip-relative displacements and rel32 branch/call targets are masked (??) so the
signature survives code moving between builds. Prints Pattern, At, the original
bytes at SITE and how many times the pattern matches (must be 1).
"""
import sys, capstone
from capstone import x86
from eboot_tool import load

def signature(t, start, end):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); md.detail = True
    out = []
    for i in md.disasm(t[start:end], start):
        b = [f'{x:02x}' for x in i.bytes]
        mask = []
        if i.disp_offset and any(op.type == x86.X86_OP_MEM and op.mem.base == x86.X86_REG_RIP for op in i.operands):
            mask.append((i.disp_offset, i.disp_size))
        if i.imm_offset and i.group(capstone.CS_GRP_BRANCH_RELATIVE) and i.imm_size == 4:
            mask.append((i.imm_offset, 4))
        for off, size in mask:
            for k in range(off, off + size): b[k] = '??'
        out += b
        if i.address + i.size >= end: break
    return out

def count(t, pat):
    fixed = [(k, int(p, 16)) for k, p in enumerate(pat) if p != '??']
    k0, run = 0, []
    # longest fixed run as anchor
    best, cur = (0, 0), None
    for k, p in enumerate(pat + ['??']):
        if p != '??':
            cur = k if cur is None else cur
        elif cur is not None:
            if k - cur > best[1] - best[0]: best = (cur, k)
            cur = None
    anchor = bytes(int(p, 16) for p in pat[best[0]:best[1]])
    n, at = 0, t.find(anchor)
    while at >= 0:
        s = at - best[0]
        if s >= 0 and all(t[s + k] == v for k, v in fixed): n += 1
        at = t.find(anchor, at + 1)
    return n

if __name__ == '__main__':
    t = load(sys.argv[1]); start, end, site = (int(x, 16) for x in sys.argv[2:5])
    pat = signature(t, start, end)
    print('Pattern="' + ' '.join(pat) + '"', f'At="{site - start}"', 'matches:', count(t, pat))
    print('original at site:', t[site:site + 12].hex(), ' Address=', hex(site + 0x400000))
