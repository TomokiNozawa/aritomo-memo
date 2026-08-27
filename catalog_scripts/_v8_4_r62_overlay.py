# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps, ImageDraw, ImageEnhance
SRC=r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
OUT=r'C:\Users\t2262\aritomo-memo\catalog_scripts'
def load(t):
    for f in os.listdir(SRC):
        if f.endswith('_%s.jpg'%t): return ImageOps.exif_transpose(Image.open(os.path.join(SRC,f)))
im=load('96').convert('RGB')
H=np.load(os.path.join(OUT,'_v8_4_r62_H.npy'))
def I(Y,Z):
    p=H@np.array([Y,Z,1.0]); return p[0]/p[2],p[1]/p[2]
def draw(box,name,scale,ys,zs):
    c=im.crop(box); c=ImageEnhance.Contrast(c).enhance(1.3)
    c=c.resize((int(c.width*scale),int(c.height*scale)),Image.LANCZOS); d=ImageDraw.Draw(c)
    ox,oy=box[0],box[1]
    for Y in ys:
        col=(255,0,0) if Y%10==0 else (255,140,0)
        a=I(Y,zs[0]); b=I(Y,zs[1])
        d.line([((a[0]-ox)*scale,(a[1]-oy)*scale),((b[0]-ox)*scale,(b[1]-oy)*scale)],fill=col,width=1)
        if Y%5==0:
            p=I(Y,zs[1]); d.text(((p[0]-ox)*scale+2,(p[1]-oy)*scale-14), str(Y), fill=col)
    for Z in range(0,260,10):
        if not (zs[0]<=Z<=zs[1]): continue
        a=I(ys[0],Z); b=I(ys[-1],Z)
        d.line([((a[0]-ox)*scale,(a[1]-oy)*scale),((b[0]-ox)*scale,(b[1]-oy)*scale)],fill=(0,150,255),width=1)
        d.text(((a[0]-ox)*scale+2,(a[1]-oy)*scale+2), 'Z%d'%Z, fill=(0,150,255))
    p=os.path.join(OUT,'_v8_4_r62_%s.png'%name); c.save(p); print(name,p,c.size)
draw((1250,0,3050,180),'ov96_sills',1.7,range(185,315,1),(150,175))
draw((3000,1050,3560,1500),'ov96_vent',2.6,range(365,425,1),(0,60))
