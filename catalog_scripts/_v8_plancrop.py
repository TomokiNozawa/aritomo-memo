# -*- coding: utf-8 -*-
import os, sys
from PIL import Image, ImageOps

OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\09_その他\間取り図_実測赤入り原本.JPG"
im = ImageOps.exif_transpose(Image.open(SRC)).convert("RGB")
print("src", im.size)
for a in sys.argv[1:]:
    name, l, t, r, b = a.split(",")[:5]
    md = int(a.split(",")[5]) if len(a.split(",")) > 5 else 1500
    c = im.crop((int(l), int(t), int(r), int(b)))
    w, h = c.size
    sc = float(md)/max(w, h)
    c = c.resize((int(w*sc), int(h*sc)), Image.LANCZOS)
    p = os.path.join(OUT, "_v8_4_rooms_plan_%s.png" % name)
    c.save(p)
    print(p, c.size)
