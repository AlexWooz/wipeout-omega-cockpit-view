#!/usr/bin/env python3
"""Build the 2048 part of "Cockpit Camera - HUD on the cockpit screens" and write it into the mod.

  build_hud2048.py ELF   (Needs: keystone-engine, capstone)

With the HUD group the game always has two HUDs (slot 0 cockpit 0xa73690, slot 1 screen 0xa73698). WipEout 2048's
HUD is filled by "driver" objects (time trial class 0x97d2d8, others 0x97d1e8/0x97d338/...), one per HUD; the race
managers create the second driver, and the constructors bind each driver to its slot, only with the race VR flag.
Without them the screen HUD shows no lap, times or team. These lines take the VR side at each of those tests:
  constructors 0x2d79f4, 0x2d8f28, 0x2d01cf and managers 0x5e30a6, 0x5e893c, 0x5d9a20, 0x5e53ed:
      cmp byte [VR],0 -> test esp,esp (ZF clear, as with VR on) + 5-byte nop
  managers 0x5d7ea8, 0x5ddace: mov dl,[VR] -> mov dl,1 + 4-byte nop
The race manager update (0x5cdb30) ticks only the first driver ([game+0x300f8], 0x5cff83); in VR the second one is
never ticked either. The hook there jumps to a cave (0x301500, in the never-run VR camera block of 0x2ffd90, past the
team-ship code) that ticks [game+0x300f8] and then [game+0x30100].
HUD messages (perfect lap, final lap...): each HUD's update (0x26b030, 0x27787e) reads the flags [[hud+0x78]+0x138] and
clears them, so the cockpit HUD took them all, hidden or not. Now it takes them only when the screen HUD (slot 1) is
hidden (bit 4 of +0x60), and hides itself when the screen HUD shows (regular ships: the camera switch never swaps the
HUDs for them, so both stayed visible and text like WRONG WAY showed twice). A cave at 0x301480 does this.
"""
import os, re, sys
import keystone
from eboot_tool import load, PATCH_BASE
from make_signature import signature, count

CMP_SITES = [0x2d79f4, 0x2d8f28, 0x2d01cf, 0x5e30a6, 0x5e893c, 0x5d9a20, 0x5e53ed]
MOV_SITES = [0x5d7ea8, 0x5ddace]
HOOK, HOOK_END, CAVE = 0x5cff83, 0x5cff9b, 0x301500
GROUP = 'Cockpit Camera - HUD on the cockpit screens'
MSG_HOOK, MSG_CAVE = 0x27787e, 0x301480
MARK = '<!-- 2048 HUD drivers (tools/build_hud2048.py) -->'

ks = keystone.Ks(keystone.KS_ARCH_X86, keystone.KS_MODE_64)

def sig(t, site, before=24, after=24):
    """Pattern/At for site, widened until unique."""
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    for span in range(before, 200, 8):
        f = t.rfind(b'\x55\x48\x89\xe5', 0, site + 1)
        ins = [i.address for i in md.disasm(t[f:site + after + 32], f)]
        start = max(a for a in ins if a <= site - span) if any(a <= site - span for a in ins) else f
        end = min(a for a in ins if a >= site + after)
        pat = signature(t, start, end)
        if count(t, pat) == 1:
            return start, ' '.join(pat)
    return None, None   # identical twin functions (0x5d96d0 / 0x5e5060): address only

def line(t, site, value):
    start, pat = sig(t, site)
    if pat is None:
        return f'<Line Type="bytes" Address="{site + PATCH_BASE:#010x}" Value="{value}"/>'
    return f'<Line Type="bytes" Address="{site + PATCH_BASE:#010x}" Value="{value}" Pattern="{pat}" At="{site - start}"/>'

def target(t, name, site, instr=None, **extra):
    start, pat = sig(t, instr if instr is not None else site)
    more = ''.join(f' {k}="{v}"' for k, v in extra.items())
    return f'<Target Name="{name}" Address="{site + PATCH_BASE:#010x}" Pattern="{pat}" At="{site - start}"{more}/>'

def build(t):
    for a in CMP_SITES: assert t[a:a + 2] == b'\x80\x3d' and t[a + 6] == 0, hex(a)
    for a in MOV_SITES: assert t[a:a + 2] == b'\x8a\x15', hex(a)
    cave = bytes(ks.asm("""
        mov rdi, qword ptr [r13 + 0x300f8]
        test rdi, rdi
        je s1
        mov rax, qword ptr [rdi]
        vmovss xmm0, dword ptr [rsp + 0x20]
        call qword ptr [rax + 0x18]
    s1:
        mov rdi, qword ptr [r13 + 0x30100]
        test rdi, rdi
        je s2
        mov rax, qword ptr [rdi]
        vmovss xmm0, dword ptr [rsp + 0x20]
        call qword ptr [rax + 0x18]
    s2:
    """, CAVE)[0])
    targets = [target(t, 'TICK_CAVE', CAVE), target(t, 'TICK_RET', HOOK_END)]
    lines = [line(t, a, '85e40f1f440000') for a in CMP_SITES] + [line(t, a, 'b2010f1f4000') for a in MOV_SITES]
    lines.append(line(t, CAVE, cave.hex() + 'e9{rel:TICK_RET:0}'))
    lines.append(line(t, HOOK, 'e9{rel:TICK_CAVE:0}' + '90' * (HOOK_END - HOOK - 5)))
    assert t[MSG_HOOK:MSG_HOOK + 16] == bytes.fromhex('8b9838010000c7803801000000000000')
    assert t[0x27a158:0x27a15b] == bytes.fromhex('48391d') and t[0x27a161:0x27a164] == bytes.fromhex('488b05')
    targets += [target(t, 'SLOT0', 0x27a15b, 0x27a158, Ref='1'), target(t, 'SLOT1', 0x27a164, 0x27a161, Ref='1'), target(t, 'MSG_CAVE', MSG_CAVE)]
    # cmp r13,[SLOT0]; jne take; mov rbx,[SLOT1]; test rbx,rbx; je take; test byte [rbx+0x60],4; je take; and byte [r13+0x60],0xfb; xor ebx,ebx; ret
    # take: mov ebx,[rax+0x138]; mov dword [rax+0x138],0; ret
    lines.append(line(t, MSG_CAVE, '4c3b2d{rel:SLOT0:0}751a488b1d{rel:SLOT1:0}4885db740ef64360047408' '418065 60fb'.replace(' ', '') + '31dbc3' '8b9838010000c7803801000000000000c3'))
    lines.append(line(t, MSG_HOOK, 'e8{rel:MSG_CAVE:0}' + '90' * 11))
    return targets, lines

if __name__ == '__main__':
    t = load(sys.argv[1])
    targets, lines = build(t)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mod', 'Cockpit Camera', 'patches', 'Cockpit_Camera.xml')
    s = open(path).read()
    m = re.search(r'(    <Metadata [^>]*Name="' + re.escape(GROUP) + r'"[^>]*>\n)(.*?)(    </Metadata>)', s, re.S)
    head, body, tail = m.groups()
    body = re.sub(r'        ' + re.escape(MARK) + r'.*?(?=        </PatchList>)', '', body, flags=re.S)   # drop an older copy
    body = re.sub(r'\s*<Target Name="(TICK_CAVE|TICK_RET|SLOT0|SLOT1|MSG_CAVE)"[^>]*/>', '', body)
    body = re.sub(r'(        <PatchList>)', '\n'.join('        ' + x for x in targets) + r'\n\1', body, count=1)
    body = body.replace('        </PatchList>', '        ' + MARK + '\n' + '\n'.join('            ' + x for x in lines) + '\n        </PatchList>')
    open(path, 'w').write(s[:m.start()] + head + body + tail + s[m.end():])
    print(len(lines), 'lines,', len(targets), 'targets written')
