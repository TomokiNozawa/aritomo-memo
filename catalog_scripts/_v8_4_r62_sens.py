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
NEf,NEr,SEf,SEr=np.load(os.path.join(OUT,'_v8_4_r62_anchors.npy'))
def homog(src,dst):
    M=[]
    for (X,Y),(u,v) in zip(src,dst):
        M.append([X,Y,1,0,0,0,-u*X,-u*Y,-u]); M.append([0,0,0,X,Y,1,-v*X,-v*Y,-v])
    _,_,V=np.linalg.svd(np.array(M)); h=V[-1].reshape(3,3); return h/h[2,2]
def mk(rail):
    w=np.array([[107,0],[107,rail],[418,0],[418,rail]],float)
    H=homog(w,np.array([NEf,NEr,SEf,SEr],float)); return np.linalg.inv(H)
def edges(Hi,y,x0,x1):
    row=A[max(0,y-3):y+4,x0:x1].mean(axis=0); thr=(row.max()+row.min())/2
    b=row>thr; runs=[]; s=None
    for i,v in enumerate(b):
        if v and s is None: s=i
        if not v and s is not None:
            if i-s>8: runs.append((s,i))
            s=None
    if s is not None and len(b)-s>8: runs.append((s,len(b)))
    def W(u,v):
        p=Hi@np.array([u,v,1.0]); return p[0]/p[2]
    return [(round(W(x0+a,y),1),round(W(x0+bb,y),1)) for a,bb in runs]
for rail in (86,88,90.6,93,96):
    Hi=mk(rail)
    print('rail=%.1f  y=8 :'%rail, edges(Hi,8,1250,3000))
    def W(u,v):
        p=Hi@np.array([u,v,1.0]); return p[0]/p[2],p[1]/p[2]
    print('        vent L(3099,1200)=%.1f R(3323,1200)=%.1f  ventbottomZ(3220,1306)=%.1f  sillZ(2300,1)=%.1f'%(
        W(3099,1200)[0],W(3323,1200)[0],W(3220,1306)[1],W(2300,1)[1]))
