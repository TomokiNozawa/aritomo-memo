# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps
SRC = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
OUT = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
def load(t):
    for f in os.listdir(SRC):
        if f.endswith('_%s.jpg'%t): return ImageOps.exif_transpose(Image.open(os.path.join(SRC,f)))
A = np.asarray(load('96').convert('L'), dtype=float)
NEf,NEr,SEf,SEr = np.load(os.path.join(OUT,'_v8_4_r62_anchors.npy'))
RAIL = 90.6
world = np.array([[107,0],[107,RAIL],[418,0],[418,RAIL]],float)
img   = np.array([NEf,NEr,SEf,SEr],float)
def homography(src,dst):
    M=[]
    for (X,Y),(u,v) in zip(src,dst):
        M.append([X,Y,1,0,0,0,-u*X,-u*Y,-u]); M.append([0,0,0,X,Y,1,-v*X,-v*Y,-v])
    _,_,V=np.linalg.svd(np.array(M)); h=V[-1].reshape(3,3); return h/h[2,2]
H = homography(world,img); Hi = np.linalg.inv(H)
def toWorld(u,v):
    p=Hi@np.array([u,v,1.0]); return p[0]/p[2], p[1]/p[2]
def toImg(X,Y):
    p=H@np.array([X,Y,1.0]); return p[0]/p[2], p[1]/p[2]
print('check anchors:')
for (X,Y),(u,v) in zip(world,img): print('  world',X,Y,'-> img',np.round(toImg(X,Y),1),'actual',np.round([u,v],1))
print('ceiling(240) at y=107 ->', np.round(toImg(107,240),1), ' y=418 ->', np.round(toImg(418,240),1))

def edge_h(y,x0,x1,sign=0):
    row=A[y-2:y+3,x0:x1].mean(axis=0); g=np.gradient(row)
    gg = np.abs(g) if sign==0 else (g if sign>0 else -g)
    i=int(np.argmax(gg))
    if 0<i<len(g)-1:
        a,b,c=gg[i-1],gg[i],gg[i+1]; d=(a-c)/(2*(a-2*b+c)) if (a-2*b+c)!=0 else 0
    else:d=0
    return x0+i+d, g[i]
def edge_v(x,y0,y1,sign=0):
    col=A[y0:y1,x-2:x+3].mean(axis=1); g=np.gradient(col)
    gg=np.abs(g) if sign==0 else (g if sign>0 else -g)
    i=int(np.argmax(gg))
    if 0<i<len(g)-1:
        a,b,c=gg[i-1],gg[i],gg[i+1]; d=(a-c)/(2*(a-2*b+c)) if (a-2*b+c)!=0 else 0
    else:d=0
    return y0+i+d, g[i]

print('\n=== VENT cover edges (photo 96) ===')
for y in (1160,1200,1240,1270):
    L,_ = edge_h(y,3060,3120, +1)     # dark wall -> bright frame
    R,_ = edge_h(y,3290,3350, -1)     # bright cover -> darker wall/shadow
    print(' row y=%d  left=%.1f (Y=%.1f)  right=%.1f (Y=%.1f)'%(y,L,toWorld(L,y)[0],R,toWorld(R,y)[0]))
for x in (3160,3220,3280):
    T,_ = edge_v(x,1090,1150,-1); B,_ = edge_v(x,1270,1330,+1)
    print(' col x=%d  top=%.1f (Z=%.1f)  bot=%.1f (Z=%.1f)'%(x,T,toWorld(x,T)[1],B,toWorld(x,B)[1]))
print('\n=== OUTLET plate (photo 96) ===')
for y in (1130,1180,1200):
    L,_=edge_h(y,3330,3380,+1); R,_=edge_h(y,3470,3520,-1)
    print(' row y=%d left=%.1f (Y=%.1f) right=%.1f (Y=%.1f)'%(y,L,toWorld(L,y)[0],R,toWorld(R,y)[0]))
for x in (3400,3440):
    T,_=edge_v(x,1080,1130,-1); B,_=edge_v(x,1190,1240,+1)
    print(' col x=%d top=%.1f (Z=%.1f) bot=%.1f (Z=%.1f)'%(x,T,toWorld(x,T)[1],B,toWorld(x,B)[1]))
np.save(os.path.join(OUT,'_v8_4_r62_H.npy'),H)
