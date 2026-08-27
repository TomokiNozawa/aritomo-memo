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
def W(u,v):
    p=Hi@np.array([u,v,1.0]); return p[0]/p[2], p[1]/p[2]
# profile across the top rows to locate the 2 windows' white casings
for y in (20,40,60,80,100):
    row=A[y-3:y+4, 1100:2900].mean(axis=0)
    g=np.gradient(row)
    idx=[i for i in range(3,len(g)-3) if abs(g[i])>12 and abs(g[i])==max(abs(g[i-3:i+4]))]
    print('y=%d edges:'%y, [(1100+i, round(g[i],1), round(W(1100+i,y)[0],1)) for i in idx])
print()
print('bottom of sill/casing scan: columns')
for x in (1550,1700,2050,2400):
    col=A[0:400, x-3:x+4].mean(axis=1); g=np.gradient(col)
    idx=[i for i in range(3,len(g)-3) if abs(g[i])>10 and abs(g[i])==max(abs(g[i-3:i+4]))]
    print(' x=%d:'%x, [(i, round(g[i],1), round(W(x,i)[1],1)) for i in idx])
