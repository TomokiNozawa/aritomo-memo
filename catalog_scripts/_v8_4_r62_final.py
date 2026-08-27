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
# 1) far right of photo 96: SE corner -> WIC wall strip -> WIC door
c=im.crop((3300,700,4000,1900)); c=ImageEnhance.Contrast(c).enhance(1.5)
c=c.resize((c.width*2,c.height*2),Image.LANCZOS)
c.save(os.path.join(OUT,'_v8_4_r62_96_wicstrip.png')); print('wicstrip', c.size)
# 2) annotated vent figure
H=np.load(os.path.join(OUT,'_v8_4_r62_H.npy'))
def I(Y,Z):
    p=H@np.array([Y,Z,1.0]); return np.array([p[0]/p[2],p[1]/p[2]])
box=(3000,1020,3600,1560); sc=2.4
c=im.crop(box); c=ImageEnhance.Brightness(c).enhance(1.15)
c=c.resize((int(c.width*sc),int(c.height*sc)),Image.LANCZOS); d=ImageDraw.Draw(c)
def P(Y,Z):
    p=I(Y,Z); return ((p[0]-box[0])*sc,(p[1]-box[1])*sc)
for Y,col,lab in [(375.0,(255,0,0),'Y=375 (WIC壁から43)'),(396.0,(255,0,0),'Y=396 (=375+21)'),
                  (418.0,(0,200,0),'Y=418 WIC側の壁'),(399.7,(255,160,0),'Y=399.7 実測カバー右端')]:
    d.line([P(Y,0),P(Y,70)],fill=col,width=3); d.text((P(Y,70)[0]-30,P(Y,70)[1]-16),lab,fill=col)
for Z,col in [(0,(0,150,255)),(24,(255,0,255)),(45,(255,0,255))]:
    d.line([P(360,Z),P(420,Z)],fill=col,width=3); d.text((6,P(360,Z)[1]-16),'Z=%d'%Z,fill=col)
c.save(os.path.join(OUT,'_v8_4_r62_vent_annotated.png')); print('vent_annotated', c.size)
