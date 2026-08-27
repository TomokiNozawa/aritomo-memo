# -*- coding: utf-8 -*-
import os
import numpy as np
from PIL import Image, ImageOps, ImageDraw
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
im=ImageOps.exif_transpose(Image.open(os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_39.jpg'))).convert('RGB')
print(im.size)
x0,y0,x1,y1=600,1150,1400,2250
s=1.6
c=im.crop((x0,y0,x1,y1)).resize((int((x1-x0)*s),int((y1-y0)*s)),Image.LANCZOS)
d=ImageDraw.Draw(c)
for oy in range(y0,y1,25):
    dy=int((oy-y0)*s); big=(oy%100==0)
    d.line([(0,dy),(70 if big else 20,dy)],fill=(255,0,0),width=2)
    if big: d.text((74,dy-8),str(oy),fill=(255,0,0))
for ox in range(x0,x1,100):
    dx=int((ox-x0)*s); d.line([(dx,0),(dx,18)],fill=(0,140,255),width=2); d.text((dx+2,20),str(ox),fill=(0,110,255))
c.save(os.path.join(OUT,'_v8_4_kit_m39_south.png')); print(c.size)
