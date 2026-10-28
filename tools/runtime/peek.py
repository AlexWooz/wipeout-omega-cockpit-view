# Client for the peek server. Usage from python: from peek import rd, wr, q, f32
import socket, json, base64, struct, os
RT = None
_s = _f = None
def _call(r):
    global _s, _f
    if _s is None:
        _s = socket.socket(socket.AF_UNIX); _s.connect('\0wipeout-peek'); _f = _s.makefile('rw')
    _f.write(json.dumps(r) + '\n'); _f.flush()
    o = json.loads(_f.readline())
    if 'error' in o: raise IOError(o['error'])
    return o
BASE = int(os.environ.get('PEEK_BASE', '0x800000000'), 0)   # host = guest + BASE
def G(a): return a + BASE   # eboot static address -> host; heap pointers are host already
def rd(a, n): return base64.b64decode(_call({'op': 'read', 'addr': a, 'len': n})['data'])
def wr(a, b): _call({'op': 'write', 'addr': a, 'data': base64.b64encode(b).decode()})
def q(a): return struct.unpack('<Q', rd(a, 8))[0]
def d(a): return struct.unpack('<I', rd(a, 4))[0]
def b(a): return rd(a, 1)[0]
def f32(a): return struct.unpack('<f', rd(a, 4))[0]
