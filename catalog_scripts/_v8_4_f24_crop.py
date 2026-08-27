# -*- coding: utf-8 -*-
import os, sys
from PIL import Image, ImageOps, ImageDraw

SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\01_リビング"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"

def up(n):
    return ImageOps.exif_transpose(Image.open(os.path.join(SRC, f"LINE_ALBUM_20260820 内覧_260820_{n}.jpg")))

def crop(n, box, name, grid=None, maxdim=1400):
    im = up(n).crop(box)
    w,h = im.size
    if grid:
        d = ImageDraw.Draw(im)
        step = grid
        for x in range(0, w, step):
            d.line([(x,0),(x,h)], fill=(255,0,0), width=2)
            d.text((x+3,3), str(box[0]+x), fill=(255,0,0))
        for y in range(0, h, step):
            d.line([(0,y),(w,y)], fill=(0,128,255), width=2)
            d.text((3,y+3), str(box[1]+y), fill=(0,128,255))
    s = float(maxdim)/max(w,h)
    if s < 1:
        im = im.resize((int(w*s), int(h*s)), Image.LANCZOS)
    p = os.path.join(OUT, name)
    im.save(p)
    print(p, im.size, "src box", box)

if __name__ == "__main__":
    crop("65", (500, 800, 1350, 3250), "_v8_4_f24_65_closet.png")
    crop("65", (500, 800, 1350, 3250), "_v8_4_f24_65_closet_grid.png", grid=100)
