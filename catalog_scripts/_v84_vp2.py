# -*- coding: utf-8 -*-
import os
import numpy as np
from PIL import Image, ImageOps
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
p=os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_38.jpg')
im=ImageOps.exif_transpose(Image.open(p)).convert('RGB')
g=np.asarray(im.convert('L'),dtype=np.float32)
H,W=g.shape

def track(x_start,y_start,y_end,step,half=18):
    xs=[];ys=[];x=float(x_start)
    rng=range(y_start,y_end,step) if step>0 else range(y_start,y_end,step)
    for y in rng:
        a=int(max(0,x-half)); b=int(min(W-1,x+half))
        row=g[y,a:b]
        if len(row)<5: break
        d=np.abs(np.diff(row))
        i=int(np.argmax(d))
        if d[i]<6: continue
        xn=a+i+0.5
        xs.append(xn); ys.append(y); x=xn
    return np.array(xs),np.array(ys)

def fit(xs,ys,label):
    A=np.vstack([ys,np.ones(len(ys))]).T
    m,c=np.linalg.lstsq(A,xs,rcond=None)[0]
    res=xs-(m*ys+c)
    print(label,'n=%d slope=%.5f x@y0=%.1f rms=%.2f'%(len(ys),m,c,np.sqrt((res**2).mean())))
    return m,c

lines={}
xs,ys=track(1673,700,1950,10); lines['colseam']=fit(xs,ys,'colseam')
xs,ys=track(150,1500,2080,8);  lines['gable']=fit(xs,ys,'gable(low)')
# right end of cabinet: find approx by scanning row y=1500 for big gradient in 3300..3900
row=g[1500,3300:3900]; d=np.abs(np.diff(row)); print('rightend cand', 3300+int(np.argmax(d)), d.max())
xs,ys=track(3300+int(np.argmax(d)),1000,1900,10); lines['rightend']=fit(xs,ys,'rightend')
# vanishing point from pairs
import itertools
for a,b in itertools.combinations(lines,2):
    m1,c1=lines[a]; m2,c2=lines[b]
    if abs(m1-m2)<1e-6: continue
    y=(c2-c1)/(m1-m2); x=m1*y+c1
    print('VP',a,b,'-> (%.0f, %.0f)'%(x,y))
