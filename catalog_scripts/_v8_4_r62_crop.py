# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps
SRC = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
OUT = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
def load(tag):
    for f in os.listdir(SRC):
        if f.endswith('_%s.jpg'%tag) or (tag=='big' and '大窓' in f) or (tag=='small' and '小窓' in f):
            return ImageOps.exif_transpose(Image.open(os.path.join(SRC,f)))
    raise SystemExit('nf '+tag)
def crop(tag, box, name, scale=1.0):
    im = load(tag); c = im.crop(box)
    if scale!=1.0: c = c.resize((int(c.width*scale), int(c.height*scale)), Image.LANCZOS)
    p = os.path.join(OUT, '_v8_4_r62_%s.png'%name); c.save(p)
    print(name, im.size, box, '->', c.size, p)
# 96 full is 4000x2250. white box around full-x 3100..3320, y 1080..1320
crop('96',(2900,900,4000,1600),'96_vent', 2.0)
crop('96',(2300,0,4000,1600),'96_right', 1.0)
crop('92',(0,1500,900,2200),'92_vent', 2.2)   # 92 upright 2250x4000; box near (170..380, 1780..1900)*? guess
