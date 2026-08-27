# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps
SRC=r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
for f in os.listdir(SRC):
    if '小窓' in f: P=os.path.join(SRC,f)
A=np.asarray(ImageOps.exif_transpose(Image.open(P)).convert('L'),float)
def eh(y,x0,x1,sign=0):
    row=A[max(0,y-1):y+2,x0:x1].mean(axis=0); g=np.gradient(row)
    gg=np.abs(g) if sign==0 else (g if sign>0 else -g)
    i=int(np.argmax(gg))
    if 0<i<len(g)-1:
        a,b,c=gg[i-1],gg[i],gg[i+1]; d=(a-c)/(2*(a-2*b+c)) if (a-2*b+c) else 0
    else:d=0
    return x0+i+d, gg[i]
def fitv(rows, xc, half, sign):
    pts=[]
    for y in rows:
        x,g=eh(y,int(xc-half),int(xc+half),sign)
        if g>6: pts.append((y,x))
    Y=np.array([p[0] for p in pts],float); X=np.array([p[1] for p in pts],float)
    for _ in range(5):
        c=np.polyfit(Y,X,1); r=X-np.polyval(c,Y); s=np.std(r); k=np.abs(r)<max(2*s,0.7)
        if k.sum()<4: break
        Y,X=Y[k],X[k]
    c=np.polyfit(Y,X,1); return c, float(np.max(np.abs(X-np.polyval(c,Y)))), len(X)
rows=list(range(530,650,6))
# outer white casing edges of the two windows (bright casing vs wall)
vlines=[]
for xc,half,sign,name in [(415,18,+1,'W1 left'),(541,18,-1,'W1 right'),(583,18,+1,'W2 left'),(735,20,-1,'W2 right')]:
    c,r,n=fitv(rows,xc,half,sign); vlines.append(c); print(name,'x=%.5f*y+%.1f'%(c[0],c[1]),'res',round(r,2),'n',n)
# vertical VP: least squares intersection of lines x = a*y + b
Amat=[];bv=[]
for a,b in vlines: Amat.append([1,-a]); bv.append(b)
Amat=np.array(Amat); bv=np.array(bv)
sol,*_=np.linalg.lstsq(Amat,bv,rcond=None); Vx,Vy=sol[0],sol[1]
print('vertical VP =', round(Vx,1), round(Vy,1))
cF=np.array([0.2621,1057.7]); cC=np.array([-0.110,514.4]); cR=np.array([0.112825,845.1946])
def inter_line_v(cv, ch):  # x=cv0*y+cv1 ; y=ch0*x+ch1
    y=(ch[0]*cv[1]+ch[1])/(1-ch[0]*cv[0]); return np.array([cv[0]*y+cv[1], y])
def cross_h(cv, Zref=240.0):
    F=inter_line_v(cv,cF); R=inter_line_v(cv,cR); C=inter_line_v(cv,cC); V=np.array([Vx,Vy])
    def d(a,b): return np.hypot(*(b-a))
    def h(P):
        return Zref * ( d(F,P)/d(P,V) ) / ( d(F,C)/d(C,V) )
    return h(R), F, R, C
for i,cv in enumerate(vlines):
    r,F,R,C = cross_h(cv)
    print('vline%d  floor%s rail%s ceil%s -> RAIL HEIGHT = %.2f cm (ceiling=240)'%(i,np.round(F,1),np.round(R,1),np.round(C,1),r))
