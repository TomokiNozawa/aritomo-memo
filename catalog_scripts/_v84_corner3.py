# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageDraw
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
im=ImageOps.exif_transpose(Image.open(os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_38.jpg'))).convert('RGB')
x0,y0,x1,y1=3350,1850,3750,2150
s=4.0
c=im.crop((x0,y0,x1,y1)).resize((int((x1-x0)*s),int((y1-y0)*s)),Image.NEAREST)
d=ImageDraw.Draw(c)
for oy in range(y0,y1,10):
    dy=int((oy-y0)*s); big=(oy%50==0)
    d.line([(0,dy),(c.width,dy)],fill=(255,0,0) if big else (255,190,190),width=2 if big else 1)
    if big: d.text((4,dy+2),str(oy),fill=(255,0,0))
for ox in range(x0,x1,10):
    dx=int((ox-x0)*s); big=(ox%50==0)
    d.line([(dx,0),(dx,c.height)],fill=(0,120,255) if big else (180,215,255),width=2 if big else 1)
    if big: d.text((dx+3,4),str(ox),fill=(0,90,255))
c.save(os.path.join(OUT,'_v8_4_kit_m38_cornerNE.png')); print(c.size)
