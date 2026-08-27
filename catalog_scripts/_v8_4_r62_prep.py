# -*- coding: utf-8 -*-
import os, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps
SRC = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
OUT = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
for f in sorted(os.listdir(SRC)):
    if not f.lower().endswith(('.jpg','.jpeg','.png')): continue
    p = os.path.join(SRC,f)
    im = Image.open(p)
    ex = im.getexif()
    ori = ex.get(274)
    im2 = ImageOps.exif_transpose(im)
    if '_' in f and f.startswith('LINE'):
        tag = f.rsplit('_',1)[-1].split('.')[0]
    else:
        tag = 'big' if '大窓' in f else 'small'
    # full view downscaled
    w,h = im2.size
    sc = 1400.0/max(w,h)
    small = im2.resize((int(w*sc), int(h*sc)), Image.LANCZOS)
    op = os.path.join(OUT, '_v8_4_r62_full_%s.png'%tag)
    small.save(op)
    print(tag, f, 'orient=',ori, 'orig=',im.size, 'upright=',im2.size, '->', op)
