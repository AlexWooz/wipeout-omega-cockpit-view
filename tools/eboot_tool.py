#!/usr/bin/env python3
"""Small helper for reading the WipEout Omega Collection eboot.

Works on the plain ELF that wipeout_pc writes to out/eboot.elf (never on the
encrypted eboot.bin). Addresses are game virtual addresses; the patch XML
"Address" attribute is that address + 0x400000.

  eboot_tool.py ELF str  TEXT...      strings containing TEXT and the code that loads them
  eboot_tool.py ELF dis  ADDR [N]     disassemble the function holding ADDR (or N instrs from ADDR)
  eboot_tool.py ELF calls ADDR...     direct call/jmp sites of a function
  eboot_tool.py ELF field OFF...      instructions using [reg + OFF] (e.g. ship struct fields)
  eboot_tool.py ELF global ADDR...    rip-relative uses of a global (e.g. the VR flag 0x1012810)
Needs: pip install capstone
"""
import re, struct, sys
import capstone

TEXT_OFF, TEXT_SIZE = 0x4000, 0x96651c   # first LOAD segment: file offset, size (vaddr 0)
PATCH_BASE = 0x400000

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
RIP = re.compile(r'rip ([+-]) (0x[0-9a-f]+)')

def load(path):
    d = open(path, 'rb').read()
    return d[TEXT_OFF:TEXT_OFF + TEXT_SIZE]

def cstr(t, a):
    if 0 <= a < len(t):
        e = t.find(b'\0', a); s = t[a:e]
        if 2 < len(s) < 100 and all(32 <= c < 127 for c in s):
            return s.decode()

def rip_target(addr, size, op):
    m = RIP.search(op)
    if m:
        return addr + size + int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)

def fmt(t, i):
    tg = rip_target(i.address, i.size, i.op_str)
    c = f'  ; -> {tg:#x} {cstr(t, tg) or ""}' if tg is not None else ''
    return f'{i.address:#x}: {i.mnemonic} {i.op_str}{c}'

def sweep(t):
    md.skipdata = True
    yield from md.disasm_lite(t, 0)
    md.skipdata = False

def cmd_str(t, words):
    refs = {}
    for a, s, mn, op in sweep(t):
        tg = rip_target(a, s, op)
        if tg is not None: refs.setdefault(tg, []).append(a)
    for w in words:
        for m in re.finditer(re.escape(w.encode()), t):
            a = m.start()
            while a > 0 and t[a - 1] != 0: a -= 1
            e = t.index(b'\0', m.start())
            print(f'{a:#x} {t[a:e][:80]!r} xrefs:', ' '.join(hex(x) for x in refs.get(a, [])[:10]))

def cmd_dis(t, addr, n=None):
    if n is None:
        start = t.rfind(b'\x55\x48\x89\xe5', 0, addr + 1)   # push rbp; mov rbp,rsp
        for i in md.disasm(t[start:start + 0x4000], start):
            print(fmt(t, i))
            if i.mnemonic == 'ret' and i.address > addr: break
    else:
        for k, i in enumerate(md.disasm(t[addr:addr + n * 15], addr)):
            if k >= n: break
            print(fmt(t, i))

def cmd_calls(t, addrs):
    for a in addrs:
        sites = [p for p in (m.start() for m in re.finditer(rb'[\xe8\xe9]', t))
                 if p + 5 <= len(t) and p + 5 + struct.unpack_from('<i', t, p + 1)[0] == a]
        print(hex(a), ' '.join(hex(s) for s in sites))

def cmd_field(t, offs):
    want = {hex(o) for o in offs}
    for a, s, mn, op in sweep(t):
        m = re.search(r'\+ (0x[0-9a-f]+)\]', op)
        if m and m.group(1) in want and 'rip' not in op:
            print(f'{a:#x}: {mn} {op}')

def cmd_global(t, addrs):
    want = set(addrs)
    for a, s, mn, op in sweep(t):
        if rip_target(a, s, op) in want:
            print(f'{a:#x}: {mn} {op}')

if __name__ == '__main__':
    if len(sys.argv) < 3: sys.exit(__doc__)
    t = load(sys.argv[1]); cmd = sys.argv[2]; args = sys.argv[3:]
    num = lambda x: int(x, 16)
    if cmd == 'str': cmd_str(t, args)
    elif cmd == 'dis': cmd_dis(t, num(args[0]), int(args[1]) if len(args) > 1 else None)
    elif cmd == 'calls': cmd_calls(t, [num(a) for a in args])
    elif cmd == 'field': cmd_field(t, [num(a) for a in args])
    elif cmd == 'global': cmd_global(t, [num(a) for a in args])
    else: sys.exit(__doc__)
