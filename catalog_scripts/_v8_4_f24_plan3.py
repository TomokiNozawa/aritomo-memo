# -*- coding: utf-8 -*-
import os
from PIL import Image
SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\実測値まとめ"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
def c(f, box, name, maxdim=1400):
    im = Image.open(os.path.join(SRC,f))
    o = im.crop(box); w,h=o.size; s=float(maxdim)/max(w,h)
    if s<1: o=o.resize((int(w*s),int(h*s)), Image.LANCZOS)
    else: o=o.resize((int(w*s),int(h*s)), Image.LANCZOS)
    p=os.path.join(OUT,name); o.save(p); print(p,o.size,box)
c("間取り図_実測値まとめ_v1.7.png",(330,880,900,1620), "_v8_4_f24_plan_f24zoom.png")
c("間取り図_実測値まとめ_v1.7.png",(200,700,1200,1700), "_v8_4_f24_plan_ldkwest.png")
