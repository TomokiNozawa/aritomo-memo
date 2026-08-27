# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageEnhance
SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\01_リビング"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
im = ImageOps.exif_transpose(Image.open(os.path.join(SRC,"LINE_ALBUM_20260820 内覧_260820_65.jpg"))).convert("RGB")
im = ImageEnhance.Brightness(im).enhance(2.0)
o = im.crop((600,1800,820,2600)); o=o.resize((o.width*3,o.height*3), Image.LANCZOS)
p=os.path.join(OUT,"_v8_4_f24_65_westedge.png"); o.save(p); print(p,o.size)
o2 = im.crop((1060,1800,1260,2600)); o2=o2.resize((o2.width*3,o2.height*3), Image.LANCZOS)
p2=os.path.join(OUT,"_v8_4_f24_65_eastedge.png"); o2.save(p2); print(p2,o2.size)
