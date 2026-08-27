# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageEnhance
SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\01_リビング"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
im = ImageOps.exif_transpose(Image.open(os.path.join(SRC,"LINE_ALBUM_20260820 内覧_260820_68.jpg"))).convert("RGB")
print("size", im.size)
o = im.crop((780, 1450, 1650, 2550))
o = ImageOps.autocontrast(o, cutoff=1)
o = o.resize((int(o.width*1.6), int(o.height*1.6)), Image.LANCZOS)
p=os.path.join(OUT,"_v8_4_f24_68_shelf.png"); o.save(p); print(p,o.size)
o2 = im.crop((500, 100, 1750, 3400))
o2 = ImageOps.autocontrast(o2, cutoff=1)
s=1400.0/3300
o2 = o2.resize((int(o2.width*s), int(o2.height*s)), Image.LANCZOS)
p2=os.path.join(OUT,"_v8_4_f24_68_open_full.png"); o2.save(p2); print(p2,o2.size)
