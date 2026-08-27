# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps

OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
srcs = {
    "plan_akaire": r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\09_その他\間取り図_実測赤入り原本.JPG",
    "plan_matome": r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\実測値まとめ\間取り図_実測値まとめ_v1.7.png",
}
for name, src in srcs.items():
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    print(name, "size", im.size)
    w, h = im.size
    sc = 1800.0 / max(w, h)
    p = os.path.join(OUT, "_v8_4_rooms_%s.png" % name)
    im.resize((int(w*sc), int(h*sc)), Image.LANCZOS).save(p)
    print("  ->", p)
