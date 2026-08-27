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
def crop(tag, box, name, scale=1.0):
    im = load(tag); c = im.crop(box)
    if scale!=1.0: c = c.resize((int(c.width*scale), int(c.height*scale)), Image.LANCZOS)
    p = os.path.join(OUT, '_v8_4_r62_%s.png'%name); c.save(p); print(name, im.size, box, c.size, p)
crop('92',(100,2050,700,2750),'92_vent', 2.4)
crop('93',(600,2000,1300,2650),'93_vent', 2.2)
crop('96',(0,0,2000,2250),'96_L', 0.7)
crop('96',(2000,0,4000,2250),'96_R', 0.7)
crop('97',(600,100,1400,700),'97_vent', 2.0)
