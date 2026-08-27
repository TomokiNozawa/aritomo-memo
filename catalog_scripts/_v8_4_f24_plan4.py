# -*- coding: utf-8 -*-
import os
from PIL import Image
SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\実測値まとめ"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
for f,tag in [("間取り図_実測値まとめ_v1.7.png","v17"),("間取り図_実測値まとめ_コンセント付き_v1.4.png","cons14")]:
    im = Image.open(os.path.join(SRC,f))
    o = im.crop((440,900,720,1260))
    o = o.resize((o.width*4, o.height*4), Image.LANCZOS)
    p=os.path.join(OUT,f"_v8_4_f24_plan_{tag}_f24x4.png"); o.save(p); print(p,o.size)
