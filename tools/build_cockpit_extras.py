#!/usr/bin/env python3
"""Build the window frame and VR camera option lines of "Cockpit Camera - Show cockpit" and write them into the mod.

  build_cockpit_extras.py ELF   (Needs: keystone-engine, capstone)

The dark struts seen from the VR cockpits are the ship's Window_glassShape part, in all nine VR models (same name
hash, first dword of the part record). The main scene draw loop (0x5f2d30) skips a part when bit 1 of +0x24 is clear
(0x5fe80a, 0x5ffb08). Both tests call a cave (0x301280, in the never-run VR camera block of 0x2ffd90) that also skips
that part while the player ship is in the internal camera and has a cockpit. Part records belong to the model file,
so other ships with that model lose the part then too.

The same run writes the VR camera option. Game Options has a "Camera settings - VR" row (setting CameraVR) that is greyed
out without the VR flag: 0x596034 now always takes the enabled side (0x59634e). The code that applies the setting to the
view lock [ship+0x6987] is in that same never-run block, partly overwritten by the caves, so the camera update (0x30100a,
where it tests the VR flag) jumps to a new cave (0x301300) that does the same: it finds the setting by name hash in the
list [[0x10ea398]+0x580] (+0 hash, +0x50 next, +0x68 value) and reads the letter after OPT_INT_LOCKED_.

That cave also makes the screen HUD the active one on ships without a cockpit. The camera switch (0x312ac2) only swaps
the two HUDs for VR liveries, so regular ships kept the cockpit HUD active: it was shown every frame (0x2fed75) next to
the screen HUD, and its on-screen elements doubled text such as the lap time readout. The swap is the same as 0x312ac2.

2048 pickup icon: without the VR flag 0x2d503d slides the pickup group from its start X to its target X, and the slide
only stops for a target left of the start. In the cockpit layout the target is to the right, so X grew without end and
the icon left the dash. A cave (0x301460) takes the VR side, which sets the target directly, while the cockpit HUD is active.

Zone ship: the Zone race manager (0x2ca89f) overwrites the team with vr_zone only with the VR flag, otherwise with zone.
The ship select has already stored the chosen team in 0x1012868 (0x5ab977), so a cave keeps vr_zone when that was chosen.
"""
import os, re, sys
import capstone, keystone
from eboot_tool import load
from build_hud2048 import line, target

SITES = [(0x5fe806, 'rdx', '488b04d0'), (0x5ffb04, 'r11', '4a8b04d8')]   # mov rax,[rax+IDX*8]; test byte [rax+0x24],1
CAVE, WINDOW_HASH = 0x301280, 0x0f4c410b
OPTION_CAVE, OPTION_HOOK, OPTION_RET, MENU_SITE = 0x301300, 0x30100a, 0x3015a9, 0x596034
CAMERAVR_HASH = 0x71339a13
PICKUP_CAVE, PICKUP_SITE = 0x301460, 0x2d503d
ZONE_CAVE, ZONE_SITE = 0x301440, 0x2ca89f
GROUP = 'Cockpit Camera - Show cockpit'
MARK = '<!-- Window frame and VR camera option (tools/build_cockpit_extras.py) -->'

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
    assert t[MENU_SITE:MENU_SITE + 2] == b'\x80\x3d' and t[OPTION_HOOK:OPTION_HOOK + 2] == b'\x8a\x05'
    assert t[0x301018:0x30101b] == bytes.fromhex('488b05')
    src = f"""
        push rcx
        push rdx
        mov rax, qword ptr [r13 + 0x78]
        test rax, rax
        jz settings
        cmp qword ptr [rax + 0x77d0], 0
        jne settings
        mov rax, qword ptr [rip + 0x11223344]
        test rax, rax
        jz settings
        mov rcx, qword ptr [rip + 0x11223344]
        test rcx, rcx
        jz settings
        cmp qword ptr [rip + 0x11223344], rax
        jne settings
        mov byte ptr [rcx + 0x26a], 1
        test byte ptr [rax + 0x60], 4
        jz hidden
        or byte ptr [rcx + 0x60], 4
    hidden:
        and byte ptr [rax + 0x60], 0xfb
        mov byte ptr [rax + 0x26a], 0
        cmp qword ptr [rip + 0x11223344], rcx
        je same
        mov dl, byte ptr [rax + 0x269]
        mov byte ptr [rcx + 0x269], dl
        mov rdx, qword ptr [rax + 0x78]
        mov qword ptr [rcx + 0x78], rdx
        mov qword ptr [rip + 0x11223344], rcx
        mov qword ptr [rip + 0x11223344], rax
    same:
        mov qword ptr [rip + 0x11223344], rcx
    settings:
        mov rcx, qword ptr [rip + 0x11223344]
        test rcx, rcx
        jz out
        mov rcx, qword ptr [rcx + 0x580]
    find:
        test rcx, rcx
        jz out
        cmp dword ptr [rcx], {CAMERAVR_HASH:#x}
        je found
        mov rcx, qword ptr [rcx + 0x50]
        jmp find
    found:
        mov cl, byte ptr [rcx + 0x77]
        mov rax, qword ptr [r13 + 0x78]
        test rax, rax
        jz out
        cmp qword ptr [rax + 0x77d8], 0
        je out
        cmp cl, 0x43
        jne not_cockpit
        mov byte ptr [rax + 0x6987], 2
        jmp out
    not_cockpit:
        cmp cl, 0x54
        jne not_track
        mov byte ptr [rax + 0x6987], 0
        jmp out
    not_track:
        cmp cl, 0x50
        jne out
        mov byte ptr [rax + 0x6987], 1
    out:
        pop rdx
        pop rcx
    """
    code = bytes(ks.asm(src, OPTION_CAVE)[0])
    assert OPTION_CAVE + len(code) + 5 <= 0x301480
    refs = ['HUD_SLOT0', 'HUD_SLOT1', 'HUD_ACTIVE', 'HUD_SHOWN', 'HUD_SHOWN', 'HUD_OTHER', 'HUD_ACTIVE', 'SETTINGS']   # in code order
    h, at = '', 0
    for i, name in zip((i for i in md.disasm(code, OPTION_CAVE) if 'rip' in i.op_str), refs):
        end = i.address - OPTION_CAVE + i.size
        h += code[at:end - 4].hex() + '{rel:%s:0}' % name; at = end
    h += code[at:].hex()
    assert code.count(bytes.fromhex('44332211')) == len(refs)
    assert t[0x312ac2:0x312ac5] == bytes.fromhex('488b05') and t[0x312ace:0x312ad1] == bytes.fromhex('488b0d')
    assert t[0x312b33:0x312b36] == t[0x312b3a:0x312b3d][:1] + b'\x89\x0d' and t[0x312b41:0x312b44] == bytes.fromhex('48890d')
    targets += [target(t, 'SETTINGS', 0x30101b, 0x301018, Ref='1'), target(t, 'OPTION_CAVE', OPTION_CAVE), target(t, 'OPTION_RET', OPTION_RET),
                target(t, 'HUD_SLOT0', 0x312ac5, 0x312ac2, Ref='1'), target(t, 'HUD_SLOT1', 0x312ad1, 0x312ace, Ref='1'),
                target(t, 'HUD_SHOWN', 0x312b36, 0x312b33, Ref='1'), target(t, 'HUD_OTHER', 0x312b3d, 0x312b3a, Ref='1'),
                target(t, 'HUD_ACTIVE', 0x312b44, 0x312b41, Ref='1')]
    lines.append(line(t, OPTION_CAVE, h + 'e9{rel:OPTION_RET:0}'))
    lines.append(line(t, OPTION_HOOK, 'e9{rel:OPTION_CAVE:0}' + '90' * 9))
    lines.append(line(t, MENU_SITE, 'e915030000' + '9090'))
    assert OPTION_CAVE + len(code) + 5 <= ZONE_CAVE and t[PICKUP_SITE:PICKUP_SITE + 2] == b'\x80\x3d'
    # mov rax,[ACTIVE]; cmp rax,[SLOT0]; sete al; cmp al,0; ret (ZF clear: VR side)
    targets.append(target(t, 'PICKUP_CAVE', PICKUP_CAVE))
    lines.append(line(t, PICKUP_CAVE, '488b05{rel:HUD_ACTIVE:0}483b05{rel:HUD_SLOT0:0}0f94c03c00c3'))
    lines.append(line(t, PICKUP_SITE, 'e8{rel:PICKUP_CAVE:0}9090'))
    assert t[ZONE_SITE:ZONE_SITE + 2] == b'\x80\x3d' and t[0x2cab79:0x2cab7c] == bytes.fromhex('488d3d')
    # push rcx; movabs rcx,"vr_zone"; cmp [TEAM],rcx; sete cl; cmp cl,0; pop rcx; ret (ZF clear: vr_zone)
    zone = '51' + '48b9' + b'vr_zone\0'.hex() + '48390d{rel:TEAM:0}' + '0f94c1' + '80f900' + '59' + 'c3'
    assert ZONE_CAVE + len(re.sub(r'\{.*?\}', '00000000', zone)) // 2 <= PICKUP_CAVE
    targets += [target(t, 'TEAM', 0x2cab7c, 0x2cab79, Ref='1'), target(t, 'ZONE_CAVE', ZONE_CAVE)]
    lines.append(line(t, ZONE_CAVE, zone))
    lines.append(line(t, ZONE_SITE, 'e8{rel:ZONE_CAVE:0}9090'))
    return targets, lines

if __name__ == '__main__':
    t = load(sys.argv[1])
    targets, lines = build(t)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mod', 'Cockpit Camera', 'patches', 'Cockpit_Camera.xml')
    s = open(path).read()
    m = re.search(r'(    <Metadata [^>]*Name="' + re.escape(GROUP) + r'"[^>]*>\n)(.*?)(    </Metadata>)', s, re.S)
    head, body, tail = m.groups()
    body = re.sub(r'        ' + re.escape(MARK) + r'.*?(?=        </PatchList>)', '', body, flags=re.S)
    body = re.sub(r'\s*<Target Name="(PLAYERS|WINDOW\d|SETTINGS|OPTION_CAVE|OPTION_RET|HUD_SLOT0|HUD_SLOT1|HUD_SHOWN|HUD_OTHER|HUD_ACTIVE|PICKUP_CAVE|TEAM|ZONE_CAVE)"[^>]*/>', '', body)
    body = re.sub(r'(        <PatchList>)', '\n'.join('        ' + x for x in targets) + r'\n\1', body, count=1)
    body = body.replace('        </PatchList>', '        ' + MARK + '\n' + '\n'.join('            ' + x for x in lines) + '\n        </PatchList>')
    open(path, 'w').write(s[:m.start()] + head + body + tail + s[m.end():])
    print(len(lines), 'lines,', len(targets), 'targets written')
