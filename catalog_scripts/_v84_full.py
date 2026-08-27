# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
def load(folder,num):
    p=os.path.join(BASE,folder,'LINE_ALBUM_20260820 内覧_260820_%s.jpg'%num)
    return ImageOps.exif_transpose(Image.open(p)).convert('RGB')
for f,n in [('03_キッチン','38'),('03_キッチン','39'),('03_キッチン','80'),('03_キッチン','34')]:
    im=load(f,n); print(n, im.size)
    im2=im.copy(); im2.thumbnail((1500,1500))
    im2.save(os.path.join(OUT,'_v8_4_kit_full_%s.png'%n))
