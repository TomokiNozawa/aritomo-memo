# -*- coding: utf-8 -*-
import os
from PIL import Image
SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\実測値まとめ"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
im = Image.open(os.path.join(SRC,"間取り図_実測値まとめ_v1.7.png"))
def c(box,name,z=2):
    o=im.crop(box); o=o.resize((int(o.width*z),int(o.height*z)), Image.LANCZOS)
    p=os.path.join(OUT,name); o.save(p); print(p,o.size,box)
c((560,880,1300,1080),"_v8_4_f24_plan_204.png",z=2)   # 204 arrow row
c((260,880,760,1620),"_v8_4_f24_plan_1995.png",z=2)   # 199.5 arrow column
