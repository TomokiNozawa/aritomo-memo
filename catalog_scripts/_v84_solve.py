# -*- coding: utf-8 -*-
import os
import numpy as np
from PIL import Image, ImageOps
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
p=os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_38.jpg')
im=ImageOps.exif_transpose(Image.open(p)).convert('RGB')
g=np.asarray(im.convert('L'),dtype=np.float32)
H,W=g.shape

def track_h(y_start,x_start,x_end,step,half=14,mode='max'):
    """follow a near-horizontal edge; returns xs,ys"""
    xs=[];ys=[];y=float(y_start)
    for x in range(x_start,x_end,step):
        a=int(max(0,y-half)); b=int(min(H-1,y+half))
        col=g[a:b,x]
        if len(col)<5: continue
        d=np.diff(col)
        i=int(np.argmax(np.abs(d)))
        if abs(d[i])<5: continue
        yn=a+i+0.5
        xs.append(x); ys.append(yn); y=yn
    return np.array(xs),np.array(ys)

def fitline(xs,ys,label):
    A=np.vstack([xs,np.ones(len(xs))]).T
    a,b=np.linalg.lstsq(A,ys,rcond=None)[0]
    r=ys-(a*xs+b)
    print('%-12s n=%3d  y=%.5f*x + %.1f   rms=%.1f'%(label,len(xs),a,b,np.sqrt((r**2).mean())))
    return a,b

L={}
L['top']    = fitline(*track_h(653, 250,1500,10), label='counterTop')     # top surface / front edge corner
L['slabbot']= fitline(*track_h(707, 250,1500,10), label='slabBottom')
L['seam1']  = fitline(*track_h(1120,250,1500,10), label='seam1_L')
L['seam2']  = fitline(*track_h(1735,250,1500,10), label='seam2_L')
print()
# right column
L['seam1R'] = fitline(*track_h(1090,1800,3300,10), label='seam1_R')
L['seam2R'] = fitline(*track_h(1700,1800,3300,10), label='seam2_R')

VPx,VPy = 1948.0, 8016.0
yf, xf = 2109.0, 355.0
mg = (VPx-xf)/(VPy-yf)     # dx/dy of gable line
def gable_y(a,b):
    # y = a*x+b  ;  x = xf + mg*(y-yf)
    return (b + a*(xf-mg*yf))/(1-a*mg)

ys={k:gable_y(*v) for k,v in L.items()}
yt = ys['top']
def h(y):
    return 85.0*((y-yf)*(VPy-yt))/((VPy-y)*(yt-yf))
print()
print('gable-line image y:', {k:round(v,1) for k,v in ys.items()}, ' floor y=%.0f'%yf)
print()
for k in ['top','slabbot','seam1','seam2','seam1R','seam2R']:
    print('%-9s img_y=%7.1f   height=%6.2f cm'%(k, ys[k], h(ys[k])))
print()
print('--- segment heights (left/sink column) ---')
print('counter slab+reveal (85 -> top of drawer front): %.2f'%(85-h(ys['slabbot'])))
print('drawer1 front  : %.2f cm'%(h(ys['slabbot'])-h(ys['seam1'])))
print('drawer2 front  : %.2f cm'%(h(ys['seam1'])-h(ys['seam2'])))
print('kick           : %.2f cm'%(h(ys['seam2'])))
print('--- right/cooktop column ---')
print('grill-tier front: %.2f cm'%(h(ys['slabbot'])-h(ys['seam1R'])))
print('lower drawer    : %.2f cm'%(h(ys['seam1R'])-h(ys['seam2R'])))
print('kick(R)         : %.2f cm'%(h(ys['seam2R'])))
print()
for vy in [6500.0,8016.0,10000.0,1e9]:
    VPy2=vy
    mg2=(VPx-xf)/(VPy2-yf)
    def gy(a,b): return (b + a*(xf-mg2*yf))/(1-a*mg2)
    yt2=gy(*L['top'])
    def h2(y): return 85.0*((y-yf)*(VPy2-yt2))/((VPy2-y)*(yt2-yf))
    seq=[h2(gy(*L[k])) for k in ['slabbot','seam1','seam2','seam1R','seam2R']]
    print('VPy=%9.0f -> slab_bot=%.1f seam1=%.1f seam2=%.1f | seam1R=%.1f seam2R=%.1f'%(vy,*seq))
