from peek import *
def elements():
    h=q(G(0xa735b0)); out=[]
    for off in range(0,0xe00,8):
        p=q(h+off)
        if 0x1000000000<=p<0x2000000000:
            try:
                if q(p)==0x800984268: out.append((off,p))
            except Exception: pass
    return h,out
def setview(v):
    h,els=elements()
    for o,p in els: wr(p+0xf8, bytes([v]))
    return len(els)
def children(o):
    c=q(o+0x20); out=[]
    while c and len(out)<200:
        out.append(c); c=q(c+0x18)
    return out
