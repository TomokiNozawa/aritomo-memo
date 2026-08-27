# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps

SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\01_リビング"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"

for n in ["54","55","56","65","66","67","68","69"]:
    p = os.path.join(SRC, f"LINE_ALBUM_20260820 内覧_260820_{n}.jpg")
    im = Image.open(p)
    ex = im.getexif()
    ori = ex.get(274, None)
    im2 = ImageOps.exif_transpose(im)
    print(n, "orig", im.size, "exif_orientation", ori, "-> upright", im2.size)
    # downscale for viewing
    w,h = im2.size
    s = 1400.0/max(w,h)
    if s < 1:
        im2v = im2.resize((int(w*s), int(h*s)), Image.LANCZOS)
    else:
        im2v = im2
    im2v.save(os.path.join(OUT, f"_v8_4_f24_full_{n}.png"))
