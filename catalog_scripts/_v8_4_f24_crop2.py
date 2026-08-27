# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageEnhance
SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\01_リビング"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
def up(n): return ImageOps.exif_transpose(Image.open(os.path.join(SRC, f"LINE_ALBUM_20260820 内覧_260820_{n}.jpg")))
def c(n, box, name, maxdim=1400, bright=1.0, auto=False):
    o = up(n).crop(box)
    if auto: o = ImageOps.autocontrast(o, cutoff=1)
    if bright!=1.0: o = ImageEnhance.Brightness(o).enhance(bright)
    w,h=o.size; s=float(maxdim)/max(w,h)
    o=o.resize((max(1,int(w*s)),max(1,int(h*s))), Image.LANCZOS)
    p=os.path.join(OUT,name); o.save(p); print(p,o.size,box)
# 65 top of closet, brightened
c("65",(550,200,1500,1500),"_v8_4_f24_65_top_bright.png",bright=2.2,auto=True)
# 65 wide room to understand geometry
c("65",(0,0,2250,4000),"_v8_4_f24_65_wide_bright.png",bright=1.7,auto=True)
# 67 closet tight
c("67",(880,900,1550,3250),"_v8_4_f24_67_closet.png")
c("67",(880,900,1550,1600),"_v8_4_f24_67_top.png",auto=True)
# 68 whole + top
c("68",(400,0,1900,3600),"_v8_4_f24_68_closet.png")
c("68",(400,0,1900,1400),"_v8_4_f24_68_top.png",auto=True)
