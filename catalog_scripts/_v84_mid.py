# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageDraw
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
im=ImageOps.exif_transpose(Image.open(os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_38.jpg'))).convert('RGB')
x0,y0,x1,y1=1200,680,2400,1180
c=im.crop((x0,y0,x1,y1)).resize((int((x1-x0)*1.6),int((y1-y0)*1.6)),Image.LANCZOS)
d=ImageDraw.Draw(c)
for ox in range(x0,x1,100):
    dx=int((ox-x0)*1.6); d.line([(dx,0),(dx,20)],fill=(255,0,0),width=2); d.text((dx+2,22),str(ox),fill=(255,0,0))
c.save(os.path.join(OUT,'_v8_4_kit_m38_midpanel.png')); print(c.size)
