#!/usr/bin/env python3
"""Check a patch XML against out/eboot.elf.

  check_patches.py ELF XML
For each Line: the Pattern must match exactly once, Pattern start + At must equal
Address - 0x400000, and the code is disassembled before and after the patch.
Exits 1 if any line fails.
Needs: pip install capstone
"""
import re, sys, capstone
import xml.etree.ElementTree as ET
from eboot_tool import load, PATCH_BASE

def main(elf, xml):
    t = load(elf)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    bad = 0
    for ln in ET.parse(xml).iter('Line'):
        if not ln.get('Pattern'):                   # address only (see the patch's notes)
            print(f'ADR {int(ln.get("Address"), 16) - PATCH_BASE:#x}  no signature, fixed address'); continue
        pat = ln.get('Pattern').split(); at = int(ln.get('At'))
        site = int(ln.get('Address'), 16) - PATCH_BASE
        val = bytes.fromhex(re.sub(r'\{rel:[^}]*\}', '00000000', ln.get('Value')))   # {rel} targets shown as 0
        rx = re.compile(b''.join(b'.' if p == '??' else re.escape(bytes([int(p, 16)])) for p in pat), re.S)
        hits = [m.start() for m in rx.finditer(t)]
        ok = hits == [site - at]
        bad += not ok
        print(f'{"OK " if ok else "BAD"} {site:#x}  matches: {", ".join(hex(h + at) for h in hits) or "none"}')
        lo = hits[0] if hits else site - at
        code = bytearray(t[lo:lo + len(pat) + 8])
        for label in ('before', 'after'):
            print(f'  {label}:')
            for i in md.disasm(bytes(code), lo):
                print(f'    {i.address:#x}  {i.bytes.hex():20} {i.mnemonic} {i.op_str}')
            code[at:at + len(val)] = val
    return 1 if bad else 0

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
