# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps
SRC=r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
for f in os.listdir(SRC):
    if '小窓' in f: P=os.path.join(SRC,f)
A=np.asarray(ImageOps.exif_transpose(Image.open(P)).convert('L'),float)
h,w=A.shape; print('img',w,h)
vh=np.array([-1486.3,677.9]); vv=np.array([408.7,6296.2])
# solve f and principal point p by assuming p on the line? use v7.0 values, then verify orthogonality
px,py,f = 571.9,1052.4,1269.4
K=np.array([[f,0,px],[0,f,py],[0,0,1.0]]); Ki=np.linalg.inv(K)
dh=Ki@np.array([vh[0],vh[1],1.0]); dh/=np.linalg.norm(dh)
dv=Ki@np.array([vv[0],vv[1],1.0]); dv/=np.linalg.norm(dv)
print('orthogonality dh.dv =', round(float(dh@dv),4))
n=np.cross(dh,dv); n/=np.linalg.norm(n)
def plane_pt(u,v,d=1.0):
    r=Ki@np.array([u,v,1.0]); lam=d/(n@r); X=lam*r; return np.array([X@dh, X@dv])
cF=np.array([2.56708351e-01,1.05944361e+03]); cR=np.array([1.12627942e-01,8.45303402e+02])
cK=np.array([-1.10744614e-01,5.14990336e+02])
cC=np.array([-1.61836857e-01,4.37378762e+02])
# scale: vertical distance floor->ceiling must be 240
p1=plane_pt(600,np.polyval(cF,600)); p2=plane_pt(600,np.polyval(cC,600))
s=240.0/abs(p2[1]-p1[1]); print('scale cm per unit =', round(s,4))
def PT(u,v):
    q=plane_pt(u,v)*s; return q
o=PT(600,np.polyval(cF,600))
def W(u,v):
    q=PT(u,v)-o; return q[0], q[1]
# sanity: rail height
for x in (400,700,900):
    print(' rail@x=%d  Z=%.2f'%(x, W(x,np.polyval(cR,x))[1]), ' curtainrail Z=%.2f'%W(x,np.polyval(cK,x))[1])
# now measure horizontal features along a horizontal line at window mid-height
def eh_all(y,x0,x1,thr_k=0.5):
    row=A[max(0,y-2):y+3,x0:x1].mean(axis=0)
    thr=(np.percentile(row,92)+np.percentile(row,8))/2
    b=row>thr; runs=[];s0=None
    for i,v in enumerate(b):
        if v and s0 is None: s0=i
        if not v and s0 is not None:
            if i-s0>4: runs.append((s0,i))
            s0=None
    if s0 is not None and len(b)-s0>4: runs.append((s0,len(b)))
    return [(x0+a,x0+bb) for a,bb in runs]
print('\nbright runs across the wall (window casings), world Y offsets from x=600 floor pt:')
for y in (560,590,620,650,530):
    rs=eh_all(y,330,820)
    print(' y=%d'%y, ['%.1f..%.1f (w=%.1f)'%(W(a,y)[0],W(b,y)[0],W(b,y)[0]-W(a,y)[0]) for a,b in rs])

print('\n=== window outer casing verticals (fitted) ===')
vl=[(0.00045,413.6),(-0.02420,550.4),(-0.03187,605.0),(-0.05530,764.1)]
names=['W1 left','W1 right','W2 left','W2 right']
for zrow in (540,580,620,660):
    ys=[]
    for (a,b) in vl:
        x=a*zrow+b; ys.append(W(x,zrow)[0])
    print(' at imgrow %d  Z=%.1f : '%(zrow, W(600,zrow)[1]),
          ' '.join('%s=%.1f'%(n,y) for n,y in zip(names,ys)),
          '| W1 width=%.1f  gap=%.1f  W2 width=%.1f  total=%.1f'%(ys[1]-ys[0], ys[2]-ys[1], ys[3]-ys[2], ys[3]-ys[0]))
# window sill / head heights again on wall plane
cFl=np.array([2.56708351e-01,1.05944361e+03])
print('\n=== heights along W1-right jamb ===')
a,b=vl[1]
for yy in range(495,700,1):
    x=a*yy+b
    prof=[A[yy, int(round(x))-6:int(round(x))+7].mean()]
import numpy as _np
for idx,(a,b) in enumerate(vl):
    yy=_np.arange(495,700)
    xs=a*yy+b
    prof=_np.array([A[int(y), int(round(xx))-7:int(round(xx))+8].mean() for y,xx in zip(yy,xs)])
    g=_np.gradient(prof)
    ed=[(int(yy[j]), round(W(xs[j],yy[j])[1],1), round(g[j],1)) for j in range(3,len(g)-3)
        if abs(g[j])>6 and abs(g[j])==max(abs(g[j-3:j+4]))]
    print(' ',names[idx], ed)
