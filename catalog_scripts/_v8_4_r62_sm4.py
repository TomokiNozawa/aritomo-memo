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
def rfit(p):
    x=np.array([q[0] for q in p],float); y=np.array([q[1] for q in p],float)
    for _ in range(6):
        c=np.polyfit(x,y,1); r=y-np.polyval(c,x); s=np.std(r); k=np.abs(r)<max(2*s,0.6)
        if k.sum()<4: break
        x,y=x[k],y[k]
    c=np.polyfit(x,y,1); return c,float(np.max(np.abs(y-np.polyval(c,x)))),len(x)
pF=[]
for x in range(200,545,15):
    yp=1057.7+0.2621*x; y,g=ev(x,int(yp-20),int(yp+20),-1)
    if g>8: pF.append((x,y))
cF,rr,nn=rfit(pF); print('floor',cF,round(rr,2),nn)
pR=[]
for x in range(300,970,20):
    yp=845.19+0.112825*x; y,g=ev(x,int(yp-20),int(yp+20),-1)
    if g>6: pR.append((x,y))
cR,rr,nn=rfit(pR); print('rail',cR,round(rr,2),nn)
VPx=(cR[1]-cF[1])/(cF[0]-cR[0]); VPy=np.polyval(cF,VPx); print('VP_h',round(VPx,1),round(VPy,1))
# curtain-rail line (previously mis-taken for ceiling)
pK=[]
for x in range(560,790,15):
    y,g=ev(x,400,470,+1)
    if g>8: pK.append((x,y))
cK,rr,nn=rfit(pK); print('curtainrail',cK,round(rr,2),nn)
# ceiling: fuzzy minimum of intensity, constrained through VP_h
pC=[]
for x in range(520,820,20):
    col=A[250:420,x-3:x+4].mean(axis=1)
    sm=np.convolve(col,np.ones(15)/15,'same')[8:-8]
    i=int(np.argmin(sm)); pC.append((x,250+8+i))
print('ceiling raw minima',pC)
# fit slope through VP
num=sum((y-VPy)*(x-VPx) for x,y in pC); den=sum((x-VPx)**2 for x,y in pC)
mC=num/den; cC=np.array([mC, VPy-mC*VPx]); print('ceiling(thru VP)',cC)
# vertical VP from window jambs
def eh(y,x0,x1,sign):
    row=A[max(0,y-1):y+2,x0:x1].mean(axis=0); g=np.gradient(row)
    gg=(g if sign>0 else -g); i=int(np.argmax(gg))
    if 0<i<len(g)-1:
        a,b,c=gg[i-1],gg[i],gg[i+1]; d=(a-c)/(2*(a-2*b+c)) if (a-2*b+c) else 0
    else:d=0
    return x0+i+d, gg[i]
def fitv(rows,xc,half,sign):
    pts=[]
    for y in rows:
        x,g=eh(y,int(xc-half),int(xc+half),sign)
        if g>6: pts.append((y,x))
    Y=np.array([p[0] for p in pts],float); X=np.array([p[1] for p in pts],float)
    for _ in range(5):
        c=np.polyfit(Y,X,1); r=X-np.polyval(c,Y); s=np.std(r); k=np.abs(r)<max(2*s,0.6)
        if k.sum()<4: break
        Y,X=Y[k],X[k]
    return np.polyfit(Y,X,1)
rows=list(range(530,650,6))
vl=[fitv(rows,415,18,+1),fitv(rows,541,18,-1),fitv(rows,583,18,+1),fitv(rows,735,20,-1)]
Am=np.array([[1,-a] for a,b in vl]); bv=np.array([b for a,b in vl])
sol,*_=np.linalg.lstsq(Am,bv,rcond=None); V=np.array([sol[0],sol[1]]); print('VP_v',np.round(V,1))
def ilv(cv,ch):
    y=(ch[0]*cv[1]+ch[1])/(1-ch[0]*cv[0]); return np.array([cv[0]*y+cv[1],y])
def height(cv, Pimg, Zref=240.0):
    F=ilv(cv,cF); C=ilv(cv,cC)
    d=lambda a,b: np.hypot(*(b-a))
    return Zref*(d(F,Pimg)/d(Pimg,V))/(d(F,C)/d(C,V))
for i,cv in enumerate(vl):
    R=ilv(cv,cR); K=ilv(cv,cK)
    print('vline%d rail=%.1f  curtainrail=%.1f'%(i,height(cv,R),height(cv,K)))
# window sill & head heights: measure along each jamb
for i,cv in enumerate(vl):
    # sill: bright->dark below window ; head: above
    yy=np.arange(500,720)
    xs=cv[0]*yy+cv[1]
    prof=np.array([A[int(y), int(round(x))-6:int(round(x))+7].mean() for y,x in zip(yy,xs)])
    g=np.gradient(prof)
    print(' vline%d strong edges:'%i, [(int(yy[j]), round(height(cv,np.array([xs[j],yy[j]])),1), round(g[j],1))
        for j in range(3,len(g)-3) if abs(g[j])>6 and abs(g[j])==max(abs(g[j-3:j+4]))])
