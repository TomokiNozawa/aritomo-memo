# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageDraw
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
p=os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_38.jpg')
im=ImageOps.exif_transpose(Image.open(p)).convert('RGB')
x0,y0,x1,y1=0,180,1600,700
c=im.crop((x0,y0,x1,y1)).resize(((x1-x0)*1,(y1-y0)*1))
c=c.resize((int((x1-x0)*1.2),int((y1-y0)*1.2)),Image.LANCZOS)
d=ImageDraw.Draw(c); s=1.2
for oy in range(y0,y1,25):
    dy=int((oy-y0)*s); big=(oy%100==0)
    d.line([(0,dy),(70 if big else 22,dy)],fill=(255,0,0),width=2)
    if big: d.text((74,dy-9),str(oy),fill=(255,0,0))
for ox in range(x0,x1,100):
    dx=int((ox-x0)*s)
    d.line([(dx,0),(dx,25)],fill=(0,140,255),width=2); d.text((dx+2,27),str(ox),fill=(0,110,255))
c.save(os.path.join(OUT,'_v8_4_kit_m38_sink.png')); print(c.size)
