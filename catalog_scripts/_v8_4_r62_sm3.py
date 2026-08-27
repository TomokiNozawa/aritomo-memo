# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps
SRC=r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
for f in os.listdir(SRC):
    if '小窓' in f: P=os.path.join(SRC,f)
A=np.asarray(ImageOps.exif_transpose(Image.open(P)).convert('L'),float)
def ev(x,y0,y1,sign=0):
    col=A[y0:y1,max(0,x-2):x+3].mean(axis=1); g=np.gradient(col)
    gg=np.abs(g) if sign==0 else (g if sign>0 else -g)
    i=int(np.argmax(gg))
    if 0<i<len(g)-1:
        a,b,c=gg[i-1],gg[i],gg[i+1]; d=(a-c)/(2*(a-2*b+c)) if (a-2*b+c) else 0
    else:d=0
    return y0+i+d, gg[i]
print('col profiles near ceiling (x, y:val) to identify junction')
for x in (600,750,900,1000):
    col=A[250:480,x-2:x+3].mean(axis=1)
    print(' x=%d'%x, ' '.join('%d:%d'%(250+i,v) for i,v in enumerate(col) if i%10==0))
