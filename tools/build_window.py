#!/usr/bin/env python3
"""Build the window frame lines of "Cockpit Camera - Show cockpit" and write them into the mod.

  build_window.py ELF   (Needs: keystone-engine, capstone)

The dark struts seen from the VR cockpits are the ship's Window_glassShape part, in all nine VR models (same name
hash, first dword of the part record). The main scene draw loop (0x5f2d30) skips a part when bit 1 of +0x24 is clear
(0x5fe80a, 0x5ffb08). Both tests call a cave (0x301280, in the never-run VR camera block of 0x2ffd90) that also skips
that part while the player ship is in the internal camera and has a cockpit. Part records belong to the model file,
so other ships with that model lose the part then too.
"""
import os, re, sys
import capstone, keystone
from eboot_tool import load, PATCH_BASE
from build_hud2048 import line, target

SITES = [(0x5fe806, 'rdx', '488b04d0'), (0x5ffb04, 'r11', '4a8b04d8')]   # mov rax,[rax+IDX*8]; test byte [rax+0x24],1
CAVE, WINDOW_HASH = 0x301280, 0x0f4c410b
GROUP = 'Cockpit Camera - Show cockpit'
MARK = '<!-- Window frame (tools/build_window.py) -->'

ks = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_64)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

def build(t):
    for a, _, b in SITES: assert t[a:a + 8] == bytes.fromhex(b + 'f6402401'), hex(a)
    src = ''.join(f"g{n}:\n mov rax, qword ptr [rax + {r}*8]\n jmp common\n" for n, (_, r, _) in enumerate(SITES)) + f"""
    common:
        cmp dword ptr [rax], {WINDOW_HASH:#x}
        jne show
        push rcx
        mov rcx, qword ptr [rip + 0x11223344]
        test rcx, rcx
        jz no
        mov rcx, qword ptr [rcx + 0x18bf0]
        test rcx, rcx
        jz no
        cmp byte ptr [rcx + 0x6983], 0
        je no
        cmp qword ptr [rcx + 0x77d0], 0
        je no
        pop rcx
        cmp eax, eax
        ret
    no:
        pop rcx
    show:
        test byte ptr [rax + 0x24], 1
        ret
    """
    code = bytes(ks.asm(src, CAVE)[0])
    ins = list(md.disasm(code, CAVE))
    stubs = [i.address for i in ins if '*8]' in i.op_str]
    mov = next(i for i in ins if i.op_str.startswith('rcx, qword ptr [rip'))
    k = mov.address - CAVE + 3
    assert t[0x3015a9:0x3015ac] == bytes.fromhex('488b05')
    targets = [target(t, 'PLAYERS', 0x3015ac, 0x3015a9, Ref='1')]
    targets += [target(t, f'WINDOW{n}', a) for n, a in enumerate(stubs)]
    lines = [line(t, CAVE, code[:k].hex() + '{rel:PLAYERS:0}' + code[k + 4:].hex())]
    lines += [line(t, a, 'e8{rel:WINDOW%d:0}909090' % n) for n, (a, _, _) in enumerate(SITES)]
    return targets, lines

if __name__ == '__main__':
    t = load(sys.argv[1])
    targets, lines = build(t)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mod', 'Cockpit Camera', 'patches', 'Cockpit_Camera.xml')
    s = open(path).read()
    m = re.search(r'(    <Metadata [^>]*Name="' + re.escape(GROUP) + r'"[^>]*>\n)(.*?)(    </Metadata>)', s, re.S)
    head, body, tail = m.groups()
    body = re.sub(r'        ' + re.escape(MARK) + r'.*?(?=        </PatchList>)', '', body, flags=re.S)
    body = re.sub(r'\s*<Target Name="(PLAYERS|WINDOW\d)"[^>]*/>', '', body)
    body = re.sub(r'(        <PatchList>)', '\n'.join('        ' + x for x in targets) + r'\n\1', body, count=1)
    body = body.replace('        </PatchList>', '        ' + MARK + '\n' + '\n'.join('            ' + x for x in lines) + '\n        </PatchList>')
    open(path, 'w').write(s[:m.start()] + head + body + tail + s[m.end():])
    print(len(lines), 'lines,', len(targets), 'targets written')
