# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps
SRC=r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
OUT=r'C:\Users\t2262\aritomo-memo\catalog_scripts'
def load(t):
    for f in os.listdir(SRC):
        if f.endswith('_%s.jpg'%t): return ImageOps.exif_transpose(Image.open(os.path.join(SRC,f)))
A=np.asarray(load('96').convert('L'),float)
H=np.load(os.path.join(OUT,'_v8_4_r62_H.npy')); Hi=np.linalg.inv(H)
def W(u,v):
    p=Hi@np.array([u,v,1.0]); return p[0]/p[2],p[1]/p[2]
X0,X1=1250,3000
for y in (6,12,18,24,30,36,42):
    row=A[max(0,y-3):y+4,X0:X1].mean(axis=0)
    thr=(np.percentile(row,90)+np.percentile(row,10))/2
    b=row>thr; runs=[];s=None
    for i,v in enumerate(b):
        if v and s is None: s=i
        if not v and s is not None:
            if i-s>10: runs.append((s,i))
            s=None
    if s is not None and len(b)-s>10: runs.append((s,len(b)))
    # merge runs separated by <25 px
    m=[]
    for r in runs:
        if m and r[0]-m[-1][1]<25: m[-1]=(m[-1][0],r[1])
        else: m.append(list(r) if False else (r[0],r[1]))
    print('y=%2d'%y, ['%.1f..%.1f (w=%.1f)'%(W(X0+a,y)[0],W(X0+bb,y)[0],W(X0+bb,y)[0]-W(X0+a,y)[0]) for a,bb in m])
print()
print('gap between the two sill boards, and Z of scan rows:')
for y in (6,18,30): print('  y=%d -> Z=%.1f'%(y, W(2000,y)[1]))
