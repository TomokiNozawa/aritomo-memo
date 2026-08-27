# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps
SRC = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
def load(t):
    for f in os.listdir(SRC):
        if f.endswith('_%s.jpg'%t): return ImageOps.exif_transpose(Image.open(os.path.join(SRC,f)))
A = np.asarray(load('96').convert('L'), dtype=float)
def edge_v(x,y0,y1,sign=-1):
    col=A[y0:y1, x-2:x+3].mean(axis=1); g=np.gradient(col)
    gg = -g if sign<0 else g
    i=int(np.argmax(gg))
    if 0<i<len(g)-1:
        a,b,c=gg[i-1],gg[i],gg[i+1]; d=(a-c)/(2*(a-2*b+c)) if (a-2*b+c)!=0 else 0
    else: d=0
    return y0+i+d, gg[i]
# north wall floor (baseboard bottom) : predicted y = 1456 - 0.935*(x-796)
print('north-wall floor line (tracking band)')
pts=[]
for x in range(560,800,15):
    yp = 1456 - 0.935*(x-796)
    y,g = edge_v(x, int(yp-45), int(yp+45), -1)
    pts.append((x,y)); print(x, round(y,1), round(g,1))
def rfit(p,deg=1):
    x=np.array([q[0] for q in p],float); y=np.array([q[1] for q in p],float)
    for _ in range(6):
        c=np.polyfit(x,y,deg); r=y-np.polyval(c,x); s=np.std(r); k=np.abs(r)<max(2*s,1.0)
        if k.sum()<4: break
        x,y=x[k],y[k]
    c=np.polyfit(x,y,deg); return c, float(np.max(np.abs(y-np.polyval(c,x)))), len(x)
cnf,r1,n1 = rfit(pts); print('N floor', cnf, 'res',round(r1,2),'n',n1)
# north wall rail: predicted y = 746 - 0.202*(x-664)
print('north-wall rail')
pts2=[]
for x in range(150,640,20):
    yp = 746 - 0.202*(x-664)
    y,g = edge_v(x, int(yp-35), int(yp+35), -1)
    pts2.append((x,y)); print(x, round(y,1), round(g,1))
cnr,r2,n2 = rfit(pts2); print('N rail', cnr, 'res',round(r2,2),'n',n2)
cf=np.array([1.27422947e-02,1.43792141e+03]); cr=np.array([-8.77710128e-03,7.53523560e+02])
cse=np.array([-0.29817,3852.2])
def inter(c1,c2):
    x=(c2[1]-c1[1])/(c1[0]-c2[0]); return np.array([x, np.polyval(c1,x)])
def inter_vh(cv,ch):
    y=(ch[0]*cv[1]+ch[1])/(1-ch[0]*cv[0]); return np.array([cv[0]*y+cv[1], y])
NEf=inter(cf,cnf); NEr=inter(cr,cnr); SEf=inter_vh(cse,cf); SEr=inter_vh(cse,cr)
print('NEf',np.round(NEf,1),'NEr',np.round(NEr,1))
print('SEf',np.round(SEf,1),'SEr',np.round(SEr,1))
np.save(r'C:\Users\t2262\aritomo-memo\catalog_scripts\_v8_4_r62_anchors.npy', np.array([NEf,NEr,SEf,SEr]))
