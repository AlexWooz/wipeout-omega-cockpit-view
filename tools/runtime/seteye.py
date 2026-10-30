#!/usr/bin/env python3
"""seteye.py X Y Z: overwrite the player ship's team-ship eye offset [ship+0x77e0] live (model space)."""
import sys, struct
from ship import ship
from peek import wr
wr(ship() + 0x77e0, struct.pack('<3f', *(float(v) for v in sys.argv[1:4])))
