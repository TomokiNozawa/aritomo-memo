# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps
SRC = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
def load(tag):
    for f in os.listdir(SRC):
        if f.endswith('_%s.jpg'%tag): return ImageOps.exif_transpose(Image.open(os.path.join(SRC,f)))
im = load('96').convert('L')
A = np.asarray(im, dtype=float)
print('shape', A.shape)

def find_edge_v(x, y0, y1, mode='max'):
    """along column x, find sub-pixel y of strongest |d/dy| in [y0,y1]"""
    col = A[y0:y1, x-2:x+3].mean(axis=1)
    g = np.gradient(col)
    i = int(np.argmax(np.abs(g)))
    # parabolic refine
    if 0 < i < len(g)-1:
        a,b,c = abs(g[i-1]), abs(g[i]), abs(g[i+1])
        d = (a-c)/(2*(a-2*b+c)) if (a-2*b+c)!=0 else 0
    else: d=0
    return y0+i+d, g[i]

# --- floor line (wall/baseboard boundary) along east wall: search band
print('--- floor/baseboard top edge (east wall) ---')
pts_floor=[]
for x in range(750, 3400, 100):
    # baseboard is bright white; wall above is darker. find the strong bright transition low in image
    y,gv = find_edge_v(x, 1300, 1560)
    pts_floor.append((x,y,gv)); print(x, round(y,1), round(gv,1))

def robust_fit(pts):
    x=np.array([p[0] for p in pts]); y=np.array([p[1] for p in pts])
    for _ in range(6):
        c=np.polyfit(x,y,1); r=y-np.polyval(c,x); s=np.std(r)
        k=np.abs(r)<max(2.0*s,1.0)
        if k.sum()<4: break
        x,y=x[k],y[k]
    c=np.polyfit(x,y,1); r=y-np.polyval(c,x)
    return c, np.max(np.abs(r)), len(x)

cf,resf,nf = robust_fit([p for p in pts_floor if p[0]>=900])
print('floor line fit', cf, 'maxres', round(resf,2), 'n', nf)

print('--- koshi-mikiri (chair rail) ---')
pts_rail=[]
for x in range(750,3400,100):
    y,gv = find_edge_v(x, 620, 820)
    pts_rail.append((x,y,gv)); print(x, round(y,1), round(gv,1))
cr,resr,nr = robust_fit(pts_rail)
print('rail line fit', cr, 'maxres', round(resr,2), 'n', nr)

# intersection = horizontal VP of east wall
ux = (cr[1]-cf[1])/(cf[0]-cr[0]); uy = np.polyval(cf,ux)
print('VP_h =', round(ux,1), round(uy,1))

def find_edge_h(y, x0, x1):
    row = A[y-2:y+3, x0:x1].mean(axis=0)
    g = np.gradient(row); i=int(np.argmax(np.abs(g)))
    if 0<i<len(g)-1:
        a,b,c=abs(g[i-1]),abs(g[i]),abs(g[i+1]); d=(a-c)/(2*(a-2*b+c)) if (a-2*b+c)!=0 else 0
    else: d=0
    return x0+i+d, g[i]

print('--- SE corner (east wall | y=418 wall) ---')
se=[]
for y in range(950,1440,30):
    x,gv = find_edge_h(y, 3420, 3620); se.append((y,x,gv)); print(y, round(x,1), round(gv,1))
cse,ress,ns = robust_fit([(p[0],p[1]) for p in se])   # x as func of y
print('SE corner fit x=%.5f*y+%.1f'%(cse[0],cse[1]),'maxres',round(ress,2),'n',ns)

print('--- NE corner (north wall | east wall) ---')
ne=[]
for y in range(500,1350,30):
    x,gv = find_edge_h(y, 590, 780); ne.append((y,x,gv)); print(y, round(x,1), round(gv,1))
cne,resn,nn = robust_fit([(p[0],p[1]) for p in ne])
print('NE corner fit x=%.5f*y+%.1f'%(cne[0],cne[1]),'maxres',round(resn,2),'n',nn)

print('--- north wall floor & rail (left of NE corner) ---')
nf_pts=[]
for x in range(300,640,20):
    y,gv=find_edge_v(x,1150,1450); nf_pts.append((x,y,gv)); print('F',x,round(y,1),round(gv,1))
cnf,rr,nn2=robust_fit(nf_pts); print('N floor fit',cnf,'maxres',round(rr,2),'n',nn2)
nr_pts=[]
for x in range(200,620,20):
    y,gv=find_edge_v(x,540,700); nr_pts.append((x,y,gv)); print('R',x,round(y,1),round(gv,1))
cnr,rr2,nn3=robust_fit(nr_pts); print('N rail fit',cnr,'maxres',round(rr2,2),'n',nn3)

def inter(c1,c2):
    x=(c2[1]-c1[1])/(c1[0]-c2[0]); return x, np.polyval(c1,x)
NEf = inter(cf,cnf); NEr = inter(cr,cnr)
print('NE corner @floor', np.round(NEf,1), ' @rail', np.round(NEr,1))
SEf = (cse[0]*0+0,0)
# SE corner: line x = cse[0]*y + cse[1]; intersect with floor line y = cf[0]x+cf[1]
def inter_vh(cv, ch):   # x=cv0*y+cv1 ; y=ch0*x+ch1
    y = (ch[0]*cv[1]+ch[1])/(1-ch[0]*cv[0]); x = cv[0]*y+cv[1]; return x,y
SEf = inter_vh(cse,cf); SEr = inter_vh(cse,cr)
print('SE corner @floor', np.round(SEf,1), ' @rail', np.round(SEr,1))
np.save(r'C:\Users\t2262\aritomo-memo\catalog_scripts\_v8_4_r62_anchors.npy',
        np.array([NEf,NEr,SEf,SEr]))
