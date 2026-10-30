#!/usr/bin/env python3
"""hudgroup.py SITE...: apply the "HUD on the cockpit screens" lines live, except the given sites (left original)."""
import sys, xml.etree.ElementTree as ET
from peek import wr, G
d = open('/home/alexwooz/Games/wipeout_pc/out/eboot.elf', 'rb').read(); img = d[0x4000:0x4000 + 0x96651c]
skip = {int(a, 16) for a in sys.argv[1:]}
r = ET.parse('/home/alexwooz/Projects/wipeout-cockpit-cam/mod/Cockpit Camera/patches/Cockpit_Camera.xml').getroot()
for md in r.iter('Metadata'):
    if md.get('Name') != 'Cockpit Camera - HUD on the cockpit screens': continue
    for ln in md.iter('Line'):
        a = int(ln.get('Address'), 16) - 0x400000; v = bytes.fromhex(ln.get('Value'))
        wr(G(a), img[a:a + len(v)] if a in skip else v); print('original' if a in skip else 'patched ', hex(a))
