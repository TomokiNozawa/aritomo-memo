# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageDraw, ImageEnhance
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
p=os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_38.jpg')
im=ImageOps.exif_transpose(Image.open(p)).convert('RGB')
c=im.crop((250,1650,3700,2160))
c=ImageEnhance.Brightness(c).enhance(2.1)
c=ImageEnhance.Contrast(c).enhance(1.6)
c=c.resize((1725,510*1725//3450))
d=ImageDraw.Draw(c)
sc=1725/3450.0
for ox in range(250,3700,250):
    dx=int((ox-250)*sc); d.line([(dx,0),(dx,14)],fill=(255,0,0),width=2); d.text((dx+2,2),str(ox),fill=(255,0,0))
for oy in range(1650,2160,50):
    dy=int((oy-1650)*sc); d.line([(0,dy),(24,dy)],fill=(0,140,255),width=2); d.text((26,dy-7),str(oy),fill=(0,110,255))
c.save(os.path.join(OUT,'_v8_4_kit_m38_kickband.png')); print(c.size)
