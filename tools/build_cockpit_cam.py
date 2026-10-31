#!/usr/bin/env python3
"""Build the "Cockpit Camera - Team ships" patch group: the internal camera of the regular team ships
moves from the bumper to the pilot's eye.

  build_cockpit_cam.py ELF [--write]   prints the <Metadata> block, or with --write replaces it in
  mod/Cockpit Camera/patches/Cockpit_Camera.xml (Needs: keystone-engine)

The new code lives in 0x301018..0x3015a9: the VR camera options block of the camera setup (0x2ffd90),
reached only when the race VR flag is set, which this port never does (no branch or pointer leads into it;
0x30100a now always skips it). Jumps between the hooks and the new code use the port's {rel:NAME:TAIL} with
Targets found by signature, so the patch does not depend on this build's layout.

Loader (0x31d7c0, the branch for liveries without a VR cockpit, 0x31d8c2): as before it clears the
VR_Cam/cockpit slots, then looks through the model's node tree (root [model+0x90], name [node+0x88]+0x10,
child +0x20, sibling +0x18) for the first node named "...Shape" with a bounding box (+0xdc min, +0xec max) whose name holds
"ilot" (pilot), else "msSh" (the AG-Systems 2048 "AG_SystemsShape", a canopy with the pilot inside), else
"lass" or "reen" (canopy glass, windscreen). Eye in model space:
  x = middle, y = max.y + DY, z = min.z + DZ   (pilot DY/DZ, AG-Systems canopy CY/CZ, glass GY/GZ)
stored in [ship+0x77e0] (the VR cockpit transform copy; only 0x329e60 reads it, after testing the VR
cockpit node [ship+0x77d8], which team ships do not have), [ship+0x77d0] = that node, view lock
[ship+0x6987] = 2. With no match the ship keeps the bumper camera.

Canopy hiding: see GLASS_NAMES.

Camera (0x322fd0, 0x323081): with a node in [ship+0x77d0] the eye is the node's world position; for team
ships (livery [+0x74d] 0) the stored offset is added along the node's world axes (which carry the model
scale), then w = 1 as the original vblendps did.
"""
import re, struct, sys
import keystone
from eboot_tool import load, PATCH_BASE
from make_signature import signature, count

DY, DZ = -0.15, 0.60      # pilot: below the top, forward of the back of the bounding box
GY, GZ = -0.45, 0.50      # canopy glass
CY, CZ = -0.30, 0.92      # AG-Systems 2048 canopy with the pilot inside (AG_SystemsShape)

ks = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_64)

def asm(src, addr):
    enc, _ = ks.asm(src, addr)
    return bytes(enc)

WALK = """
    walk:
        test rdi, rdi
        je wret
        mov rsi, qword ptr [rdi + 0x88]
        test rsi, rsi
        je kids
        add rsi, 0x10
        vmovss xmm3, dword ptr [rdi + 0xf0]
        vucomiss xmm3, dword ptr [rdi + 0xe0]
        jbe kids
        xor r11d, r11d
    scan:
        mov eax, dword ptr [rsi]
        test al, al
        je ended
        test r11d, r11d
        jne next
        or eax, 0x20202020
        cmp eax, 0x746f6c69
        jne c2
        mov r11d, 1
        jmp next
    c2:
        cmp eax, 0x6873736d
        jne c3
        mov r11d, 2
        jmp next
    c3:
        cmp eax, 0x7373616c
        je c3y
        cmp eax, 0x6e656572
        jne next
    c3y:
        mov r11d, 3
    next:
        inc rsi
        jmp scan
    ended:
        test r11d, r11d
        je kids
        cmp dword ptr [rsi - 4], 0x65706168
        jne kids
        cmp byte ptr [rsi - 5], 0x53
        jne kids
        cmp r11d, 2
        je is2
        ja is3
        test r8, r8
        jne kids
        mov r8, rdi
        jmp kids
    is2:
        test r10, r10
        jne kids
        mov r10, rdi
        jmp kids
    is3:
        test r9, r9
        jne kids
        mov r9, rdi
    kids:
        push rdi
        mov rdi, qword ptr [rdi + 0x20]
        call walk
        pop rdi
        mov rdi, qword ptr [rdi + 0x18]
        jmp walk
    wret:
        ret
"""

def loader(base, consts):
    """Entry of the loader hook; ends with the jmp back (its rel32 is replaced by {rel:LOADER_RET:0})."""
    return f"""
        vxorps xmm0, xmm0, xmm0
        vmovups xmmword ptr [r15 + 0x77d0], xmm0
        mov word ptr [r15 + 0x77f8], 0xffff
        mov qword ptr [r15 + 0x77f0], -1
        push rax
        push rcx
        push rdx
        push rsi
        push rdi
        push r8
        push r9
        push r10
        push r11
        sub rsp, 0x38
        vmovups xmmword ptr [rsp], xmm1
        vmovups xmmword ptr [rsp + 0x10], xmm2
        vmovups xmmword ptr [rsp + 0x20], xmm3
        mov rax, qword ptr [r15 + 0x7790]
        test rax, rax
        je done
        mov rdi, qword ptr [rax + 0x90]
        xor r8d, r8d
        xor r9d, r9d
        xor r10d, r10d
        call {base:#x}
        lea rdx, [rip + {consts:#x}]
        mov rdi, r8
        test rdi, rdi
        jne have
        add rdx, 16
        mov rdi, r10
        test rdi, rdi
        jne have
        sub rdx, 8
        mov rdi, r9
        test rdi, rdi
        je done
    have:
        vmovss xmm0, dword ptr [rdi + 0xdc]
        vaddss xmm0, xmm0, dword ptr [rdi + 0xec]
        mov eax, 0x3f000000
        vmovd xmm3, eax
        vmulss xmm0, xmm0, xmm3
        vmovss xmm1, dword ptr [rdi + 0xf0]
        vaddss xmm1, xmm1, dword ptr [rdx]
        vmovss xmm2, dword ptr [rdi + 0xe4]
        vaddss xmm2, xmm2, dword ptr [rdx + 4]
        vmovss dword ptr [r15 + 0x77e0], xmm0
        vmovss dword ptr [r15 + 0x77e4], xmm1
        vmovss dword ptr [r15 + 0x77e8], xmm2
        mov dword ptr [r15 + 0x77ec], 0
        mov qword ptr [r15 + 0x77d0], rdi
        mov byte ptr [r15 + 0x6987], 2
    done:
        vmovups xmm1, xmmword ptr [rsp]
        vmovups xmm2, xmmword ptr [rsp + 0x10]
        vmovups xmm3, xmmword ptr [rsp + 0x20]
        add rsp, 0x38
        pop r11
        pop r10
        pop r9
        pop r8
        pop rdi
        pop rsi
        pop rdx
        pop rcx
        pop rax
        vxorps xmm0, xmm0, xmm0
    """

CAMERA = """
        vmovups xmm0, xmmword ptr [rax + 0x30]
        mov rcx, qword ptr [r15 + 0x6e10]
        cmp byte ptr [rcx + 0x74d], 0
        jne w1
        vbroadcastss xmm1, dword ptr [r15 + 0x77e0]
        vmulps xmm1, xmm1, xmmword ptr [rax]
        vaddps xmm0, xmm0, xmm1
        vbroadcastss xmm1, dword ptr [r15 + 0x77e4]
        vmulps xmm1, xmm1, xmmword ptr [rax + 0x10]
        vaddps xmm0, xmm0, xmm1
        vbroadcastss xmm1, dword ptr [r15 + 0x77e8]
        vmulps xmm1, xmm1, xmmword ptr [rax + 0x20]
        vaddps xmm0, xmm0, xmm1
    w1:
        mov ecx, 0x3f800000
        vmovd xmm1, ecx
        vinsertps xmm0, xmm0, xmm1, 0x30
"""

# Canopy hiding in the cockpit view of team ships. The main scene draw loop (0x5f2d30) takes each part record of a
# model (holder+0x40 list; record: +0 name hash, +0x18 name, +0x24 show bits) and skips it when bit 1 of +0x24 is
# clear (0x5fe80a, 0x5ffb08). Part records belong to the model file, not to a ship, so every ship with that model
# loses the part while the player is in the internal camera of a team ship. The first dword of a record is the
# hash of its name; these are the canopy/glass/windscreen parts of the HD and 2048 ship models (ship*.rcsmodel),
# without dash screens and the VR ships' window parts.
GLASS_NAMES = {
    'AG_Systems_AGILITY_GlassShape': 0x0c1d7bd7,
    'AG_Systems_GlassShape': 0xb42bcd34,
    'AG_Systems_PROTO_GlassShape': 0x7ea89e3f,
    'AG_Systems_SPEED_GlassShape': 0x35d29a96,
    'Auricom_Glass1Shape': 0xdd1dcbc3,
    'Auricom_GlassShape': 0xe5baadf3,
    'CanopyShape': 0x620b1d71,
    'Cockpit_GlassShape': 0x0e5d8fcd,
    'FEISAR_GlassShape': 0x742e8c0d,
    'FEISAR_PerspexShape': 0x83bc800e,
    'Feisar_Glass1Shape': 0x48cac4cd,
    'Feisar_GlassShape': 0x8dff213b,
    'GOTEKI_GlassShape': 0x66f2482f,
    'GOTEKI_PerspexShape': 0xb807d25b,
    'Glass0Shape': 0xca3e4fcf,
    'Glass1Shape': 0x01629c6a,
    'Glass2Shape': 0x87f6eec4,
    'Glass4Shape': 0x51af0dd9,
    'GlassShape': 0x4ce0cbdd,
    'GlassShape1': 0xa9f04e98,
    'GlassShape2': 0x30f91f22,
    'Glass_overShape': 0xdcc211b8,
    'PerspexShape': 0xea3ca9ec,
    'Pir_hana_GlassShape': 0xf21aa4e1,
    'Qirex_Glass1Shape': 0x823d8845,
    'SHIP_GlassShape': 0x78982f6d,
    'Ship_GlassShape': 0x1eb3c7b8,
    'WindscreenShape': 0xea930264,
    'Windscreen_stripShape': 0x8552adff,
    'glassShape': 0x03bdc80d,
    'glassShape6': 0xb10854ec,
    'pasted__Ship_Glass1Shape': 0xc86b87a1,
    'windscreenShape': 0x62563cfa,
}
GLASS_SITES = [(0x5fe806, 'rdx'), (0x5ffb04, 'r11')]   # mov rax,[rax+IDX*8]; test byte [rax+0x24],1 (8 bytes)

def glass(base, table):
    stubs = ''.join(f"g{n}:\n mov rax, qword ptr [rax + {r}*8]\n jmp common\n" for n, (_, r) in enumerate(GLASS_SITES))
    return stubs + f"""
    common:
        test byte ptr [rax + 0x24], 1
        jz done
        push rcx
        push rdx
        mov rcx, qword ptr [rip + 0x11223344]
        test rcx, rcx
        jz no
        mov rcx, qword ptr [rcx + 0x18bf0]
        test rcx, rcx
        jz no
        cmp byte ptr [rcx + 0x6983], 0
        je no
        mov rdx, qword ptr [rcx + 0x6e10]
        cmp byte ptr [rdx + 0x74d], 0
        jne no
        mov ecx, dword ptr [rax]
        lea rdx, [rip + {table:#x}]
    scan:
        cmp dword ptr [rdx], 0
        je no
        cmp ecx, dword ptr [rdx]
        je hide
        add rdx, 4
        jmp scan
    hide:
        pop rdx
        pop rcx
        cmp eax, eax
        ret
    no:
        pop rdx
        pop rcx
        test byte ptr [rax + 0x24], 1
    done:
        ret
"""

def glass_block(base):
    """Hex (with {rel:PLAYERS:0} for the players global 0xa78e98) and the stub offsets."""
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    code = asm(glass(base, 0x7fff0000), base)
    lea = next(i for i in md.disasm(code, base) if i.mnemonic == 'lea' and 'rip' in i.op_str)
    tbl = base + len(code); tbl += -tbl % 4
    code = asm(glass(base, tbl - (lea.address + lea.size)), base)
    assert base + len(code) <= tbl
    stubs = [i.address - base for i in md.disasm(code, base) if '*8]' in i.op_str]
    mov = next(i for i in md.disasm(code, base) if i.op_str.startswith('rcx, qword ptr [rip'))
    k = mov.address - base + 3                                       # the disp32 of mov rcx,[rip+disp]
    h = code[:k].hex() + '{rel:PLAYERS:0}' + code[k + 4:].hex() + 'cc' * (tbl - base - len(code))
    h += b''.join(struct.pack('<I', v) for v in GLASS_NAMES.values()).hex() + '00000000'
    return h, stubs

def jmp_rel(name):
    return 'e9{rel:' + name + ':0}'

def cave(base):
    """The bytes placed at base (as hex with {rel} placeholders), and the offsets of the two entries."""
    walk = asm(WALK, base)
    a = base + len(walk)
    # the constants follow the jmp back; lea rdx,[rip+D] gets D from a first pass that finds the lea
    body = asm(loader(base, 0x11223344), a)
    lea = body.index(bytes.fromhex('488d15') + struct.pack('<I', 0x11223344))
    consts = a + len(body) + 5
    body = asm(loader(base, consts - (a + lea + 7)), a)
    assert len(body) == lea + len(body) - lea and body[lea:lea + 3] == bytes.fromhex('488d15')
    data = struct.pack('<6f', DY, DZ, GY, GZ, CY, CZ)
    b = consts + len(data)
    b += -b % 16
    cam = asm(CAMERA, b)
    pad = b - (consts + len(data))
    hexs = walk.hex() + body.hex() + jmp_rel('LOADER_RET') + data.hex() + 'cc' * pad + cam.hex() + jmp_rel('CAMERA_RET')
    return hexs, a - base, b - base, consts - base

def site(t, start, end, at, name=None, tag='Line', **extra):
    pat = signature(t, start, end)
    assert count(t, pat) == 1, (hex(start), count(t, pat))
    attrs = f'Address="{at + PATCH_BASE:#010x}" Pattern="{" ".join(pat)}" At="{at - start}"'
    for k, v in extra.items(): attrs += f' {k}="{v}"'
    return f'<{tag} Name="{name}" {attrs}/>' if tag == 'Target' else attrs

def unique_site(t, at, point=None, name=None, tag='Line', **extra):
    """site() over instruction-aligned ranges around instruction at, widened until the signature is unique;
    the site itself is point (default at)."""
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    f = t.rfind(b'\x55\x48\x89\xe5', 0, at + 1)
    ins = [i.address for i in md.disasm(t[f:at + 0x80], f)]
    k = ins.index(at)
    for back in range(2, 40, 2):
        start, end = ins[max(0, k - back)], ins[min(len(ins) - 1, k + 4)]
        pat = signature(t, start, end)
        if count(t, pat) == 1:
            return site(t, start, end, at if point is None else point, name, tag, **extra)
    raise SystemExit(f'no unique signature at {at:#x}')

def build(t):
    CAVE = 0x301018
    hexs, ent_a, ent_b, consts = cave(CAVE)
    size = len(bytes.fromhex(''.join(p for p in hexs.replace('{', '|{').replace('}', '}|').split('|') if not p.startswith('{')))) + 4 * hexs.count('{')
    assert CAVE + size <= 0x3015a9, hex(CAVE + size)
    out = []
    out.append('<Metadata Title="WipEout Omega Collection" Name="Cockpit Camera - Team ships" '
               'Note="The internal camera of the regular team ships sits at the pilot\'s eye (or under the canopy) instead of on the bumper." '
               'Author="Alex" PatchVer="0.8" AppVer="01.00" AppElf="eboot.bin" isEnabled="true">')
    out.append('    <!-- Built by tools/build_cockpit_cam.py, which holds the assembly and the notes. -->')
    out.append('    ' + site(t, 0x300ff6, 0x301031, 0x301018, 'CAVE', 'Target'))
    out.append('    ' + site(t, 0x300ff6, 0x301031, 0x301018 + ent_a, 'LOADER_CODE', 'Target'))
    out.append('    ' + site(t, 0x300ff6, 0x301031, 0x301018 + ent_b, 'CAMERA_CODE', 'Target'))
    out.append('    ' + site(t, 0x31d8a0, 0x31d8e9, 0x31d8e5, 'LOADER_RET', 'Target', Ref='1'))
    out.append('    ' + site(t, 0x323053, 0x3230a0, 0x323090, 'CAMERA_RET', 'Target'))
    out.append('    <PatchList>')
    out.append('        <!-- Camera setup: the VR options block 0x301018 is never run (jmp past it); it holds the new code. -->')
    out.append('        <Line Type="bytes" ' + site(t, 0x300ff6, 0x301031, 0x30100a) + ' Value="e9{rel:SKIP:0}' + '90' * 9 + '"/>')
    out.append('        <Line Type="bytes" ' + site(t, 0x300ff6, 0x301031, 0x301018) + f' Value="{hexs}"/>')
    out.append('        <!-- Loader, liveries without a VR cockpit: search the pilot/canopy and set the eye. -->')
    out.append('        <Line Type="bytes" ' + site(t, 0x31d8a0, 0x31d8e9, 0x31d8c2) + ' Value="e9{rel:LOADER_CODE:0}' + 'cc' * 34 + '"/>')
    out.append('        <!-- Internal camera eye from the node: add the team ship offset. -->')
    out.append('        <Line Type="bytes" ' + site(t, 0x323053, 0x3230a0, 0x323081) + ' Value="e9{rel:CAMERA_CODE:0}' + '90' * 10 + '"/>')
    gbase = CAVE + size; gbase += -gbase % 16
    ghex, gstubs = glass_block(gbase)
    gsize = len(bytes.fromhex(re.sub(r'\{[^}]*\}', '00000000', ghex)))
    assert gbase + gsize <= 0x301500, hex(gbase + gsize)                  # the 2048 HUD tick cave starts there
    out.append('        <!-- Canopy hiding: the scene draw loop asks the code below whether to draw a part. -->')
    out.append('        <Line Type="bytes" ' + site(t, 0x300ff6, 0x301031, gbase) + f' Value="{ghex}"/>')
    for n, (at, _) in enumerate(GLASS_SITES):
        out.append('        <Line Type="bytes" ' + unique_site(t, at) + ' Value="e8{rel:GLASS%d:0}909090"/>' % n)
    out.append('    </PatchList>')
    out.append('</Metadata>')
    targets = [site(t, 0x300ff6, 0x301031, gbase + o, f'GLASS{n}', 'Target') for n, o in enumerate(gstubs)]
    targets.append(unique_site(t, 0x3015a9, 0x3015ac, 'PLAYERS', 'Target', Ref='1'))   # mov rax,[rip -> 0xa78e98]
    for x in reversed(targets): out.insert(3, '    ' + x)
    skip = site(t, 0x300ff6, 0x301031, 0x301014, 'SKIP', 'Target', Ref='1')
    out.insert(3, '    ' + skip)
    return '\n'.join(out), consts

if __name__ == '__main__':
    xml, consts = build(load(sys.argv[1]))
    if '--write' in sys.argv:
        import os, re
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mod', 'Cockpit Camera', 'patches', 'Cockpit_Camera.xml')
        old = open(path).read()
        block = '\n'.join('    ' + l for l in xml.split('\n'))
        new, n = re.subn(r'    <Metadata [^>]*Name="Cockpit Camera - Team ships".*?</Metadata>', lambda m: block, old, flags=re.S)
        assert n == 1, n
        open(path, 'w').write(new)
    else:
        print(xml)
    print(f'<!-- constants (DY, DZ, GY, GZ, CY, CZ) at {0x301018 + consts:#x} -->', file=sys.stderr)
