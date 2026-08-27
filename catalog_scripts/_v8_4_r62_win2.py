# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps
SRC = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
OUT = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
def load(t):
    for f in os.listdir(SRC):
        if f.endswith('_%s.jpg'%t): return ImageOps.exif_transpose(Image.open(os.path.join(SRC,f)))
A=np.asarray(load('96').convert('L'),float)
H=np.load(os.path.join(OUT,'_v8_4_r62_H.npy')); Hi=np.linalg.inv(H)
def Wd(u,v):
    p=Hi@np.array([u,v,1.0]); return p[0]/p[2],p[1]/p[2]
for y in (4,10,16,24,32):
    row=A[max(0,y-3):y+4,1250:2700].mean(axis=0)
    thr=(row.max()+row.min())/2
    b=row>thr; runs=[]; s=None
    for i,v in enumerate(b):
        if v and s is None: s=i
        if not v and s is not None:
            if i-s>8: runs.append((s,i)); 
            s=None
    if s is not None and len(b)-s>8: runs.append((s,len(b)))
    print('y=%d thr=%.0f bright runs (worldY):'%(y,thr),
          [(round(Wd(1250+a,y)[0],1), round(Wd(1250+bb,y)[0],1)) for a,bb in runs])
# sill board bottom edge -> world Z, sampled
print()
for x in range(1400,2600,100):
    col=A[0:200,x-3:x+4].mean(axis=1); g=np.gradient(col)
    i=int(np.argmin(g))   # bright sill -> dark wall
    print(' x=%d sillboard bottom imgy=%d  Z=%.1f'%(x,i,Wd(x,i)[1]))
