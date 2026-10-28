from peek import *
import struct
def ship(): return q(q(G(0xa78e98))+0x18bf0)
def meshes():
    s=ship(); res=q(s+0x7790); idx=struct.unpack('<i',rd(res+0x3f38,4))[0]
    m=q(q(G(0xedf3e0)+idx*0x360+0x118)); n=struct.unpack('<H',rd(m+0x38,2))[0]; arr=q(m+0x40)
    return [q(arr+i*8) for i in range(n)]
def setmesh(i, v): wr(meshes()[i]+0x24, struct.pack('<I', v))
