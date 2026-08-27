# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps
SRC=r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
for f in os.listdir(SRC):
    if '小窓' in f: P=os.path.join(SRC,f)
A=np.asarray(ImageOps.exif_transpose(Image.open(P)).convert('L'),float)
print('shape',A.shape)
def ev(x,y0,y1,sign=0):
    y0=max(0,y0); y1=min(A.shape[0],y1)
    col=A[y0:y1,max(0,x-2):x+3].mean(axis=1); g=np.gradient(col)
    gg=np.abs(g) if sign==0 else (g if sign>0 else -g)
    i=int(np.argmax(gg))
    if 0<i<len(g)-1:
        a,b,c=gg[i-1],gg[i],gg[i+1]; d=(a-c)/(2*(a-2*b+c)) if (a-2*b+c) else 0
    else: d=0
    return y0+i+d, gg[i]
def eh(y,x0,x1,sign=0):
    row=A[max(0,y-2):y+3,x0:x1].mean(axis=0); g=np.gradient(row)
    gg=np.abs(g) if sign==0 else (g if sign>0 else -g)
    i=int(np.argmax(gg))
    if 0<i<len(g)-1:
        a,b,c=gg[i-1],gg[i],gg[i+1]; d=(a-c)/(2*(a-2*b+c)) if (a-2*b+c) else 0
    else: d=0
    return x0+i+d, gg[i]
def rfit(p):
    x=np.array([q[0] for q in p],float); y=np.array([q[1] for q in p],float)
    for _ in range(6):
        c=np.polyfit(x,y,1); r=y-np.polyval(c,x); s=np.std(r); k=np.abs(r)<max(2*s,0.8)
        if k.sum()<4: break
        x,y=x[k],y[k]
    c=np.polyfit(x,y,1); return c,float(np.max(np.abs(y-np.polyval(c,x)))),len(x)
print('--- floor line (baseboard bottom) east wall ---')
p=[]
for x in range(200,980,40):
    yp = 1108 + (x-81)*(1231-1108)/(946-81)
    y,g=ev(x,int(yp-25),int(yp+25),-1); p.append((x,y)); print(x,round(y,1),round(g,1))
cF,r,n=rfit(p); print('floor',cF,round(r,2),n)
print('--- ceiling junction ---')
p=[]
for x in range(560,1040,30):
    y,g=ev(x,330,470,+1); p.append((x,y)); print(x,round(y,1),round(g,1))
cC,r,n=rfit(p); print('ceil',cC,round(r,2),n)
print('--- rail (koshi-mikiri) ---')
p=[]
for x in range(300,1000,40):
    yp = 875 + (x-300)*(960-875)/(1000-300)
    y,g=ev(x,int(yp-35),int(yp+35),-1); p.append((x,y)); print(x,round(y,1),round(g,1))
cR,r,n=rfit(p); print('rail',cR,round(r,2),n)
np.save(r'C:\Users\t2262\aritomo-memo\catalog_scripts\_v8_4_r62_smlines.npy',np.array([cF,cC,cR]))
