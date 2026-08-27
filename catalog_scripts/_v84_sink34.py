# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
im=ImageOps.exif_transpose(Image.open(os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_34.jpg'))).convert('RGB')
print(im.size)
c=im.crop((1650,1550,3000,2200)).resize((1350*2,650*2),Image.LANCZOS)
c.save(os.path.join(OUT,'_v8_4_kit_m34_sink.png')); print(c.size)
