# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageDraw, ImageEnhance
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
def load(f,n):
    return ImageOps.exif_transpose(Image.open(os.path.join(BASE,f,'LINE_ALBUM_20260820 内覧_260820_%s.jpg'%n))).convert('RGB')
im=load('03_キッチン','80'); print(im.size)
# tape runs roughly from (1250,1600) to (2700,1620) in 4000x2250
for i,(x0,y0,x1,y1) in enumerate([(1150,1500,2100,1750),(2000,1500,3000,1800),(2600,1550,3400,2250)]):
    c=im.crop((x0,y0,x1,y1))
    c=c.resize(((x1-x0)*3,(y1-y0)*3), Image.LANCZOS)
    c=ImageEnhance.Contrast(ImageEnhance.Brightness(c).enhance(1.35)).enhance(1.6)
    c.save(os.path.join(OUT,'_v8_4_kit_tape80_%d.png'%i)); print(i,c.size)
