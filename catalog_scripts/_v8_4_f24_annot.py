# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageDraw, ImageEnhance
SRC = r"C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\01_リビング"
OUT = r"C:\Users\t2262\aritomo-memo\catalog_scripts"
im = ImageOps.exif_transpose(Image.open(os.path.join(SRC,"LINE_ALBUM_20260820 内覧_260820_65.jpg"))).convert("RGB")
im = ImageEnhance.Brightness(im).enhance(1.55)
d = ImageDraw.Draw(im)
R=(255,0,0); G=(0,220,0); B=(0,140,255); Y=(255,220,0)
# vertical lines
for x,col,lab in [(688,R,"closet W edge 688"),(708,Y,"door leaf L 708"),(1112,Y,"door leaf R 1112"),(1186,R,"closet E edge 1186")]:
    d.line([(x,900),(x,3100)], fill=col, width=6)
    d.text((x+8, 1000), lab, fill=col)
# horizontal lines
for y,col,lab in [(941,B,"ceiling 941"),(1313,G,"door top 1313"),(3013,G,"door bottom 3013"),(3026,B,"floor ~3026")]:
    d.line([(600,y),(1300,y)], fill=col, width=6)
    d.text((1210, y-40), lab, fill=col)
o=im.crop((450,750,1450,3250)); o=o.resize((int(o.width*0.56),int(o.height*0.56)), Image.LANCZOS)
p=os.path.join(OUT,"_v8_4_f24_65_annotated.png"); o.save(p); print(p,o.size)
