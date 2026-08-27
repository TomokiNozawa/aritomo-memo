# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageDraw
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
p=os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_38.jpg')
im=ImageOps.exif_transpose(Image.open(p)).convert('RGB')
W,H=im.size; print(W,H)   # 4000x2250
# left column region (sink side front) full height
c=im.crop((0,500,1800,2250)).resize((1440,1400))
d=ImageDraw.Draw(c)
for y in range(0,1400,50):
    d.line([(0,y),(30,y)],fill=(255,0,0),width=2)
    d.text((34,y-7),str(int(500+y*(1750/1400))),fill=(255,0,0))
c.save(os.path.join(OUT,'_v8_4_kit_c38_left.png'))
# right column (cooktop/grill side)
c2=im.crop((1700,500,4000,2250)).resize((1600,1216))
d2=ImageDraw.Draw(c2)
for y in range(0,1216,50):
    d2.line([(0,y),(30,y)],fill=(255,0,0),width=2)
    d2.text((34,y-7),str(int(500+y*(1750/1216))),fill=(255,0,0))
c2.save(os.path.join(OUT,'_v8_4_kit_c38_right.png'))
