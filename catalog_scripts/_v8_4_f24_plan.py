# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps
SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\実測値まとめ"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
for f in ["間取り図_実測値まとめ_v1.7.png","間取り図_実測値まとめ_コンセント付き_v1.4.png"]:
    im = Image.open(os.path.join(SRC,f))
    print(f, im.size, im.mode)

im = Image.open(os.path.join(SRC,"間取り図_実測値まとめ_v1.7.png"))
w,h = im.size
s = 1500.0/max(w,h)
im.resize((int(w*s),int(h*s)), Image.LANCZOS).save(os.path.join(OUT,"_v8_4_f24_plan_v17_full.png"))
print("saved full")
