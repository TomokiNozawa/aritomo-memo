# -*- coding: utf-8 -*-
import os
from PIL import Image
SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\実測値まとめ"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
im = Image.open(os.path.join(SRC,"間取り図_実測値まとめ_v1.7.png"))
def c(box, name, maxdim=1500):
    o = im.crop(box); w,h=o.size; s=float(maxdim)/max(w,h)
    if s<1: o=o.resize((int(w*s),int(h*s)), Image.LANCZOS)
    p=os.path.join(OUT,name); o.save(p); print(p,o.size,box)
c((1080,650,2300,1650), "_v8_4_f24_plan_ldk.png")
c((1700,950,2300,1500), "_v8_4_f24_plan_ldk_ne.png")
