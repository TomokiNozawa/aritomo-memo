# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps, ImageDraw
SRC = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等\04_6.2帖'
OUT = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
def load(tag):
    for f in os.listdir(SRC):
        if f.endswith('_%s.jpg'%tag) or (tag=='big' and '大窓' in f) or (tag=='small' and '小窓' in f):
            return ImageOps.exif_transpose(Image.open(os.path.join(SRC,f)))
def grid(tag, box, name, scale, step):
    im = load(tag); c = im.crop(box).convert('RGB')
    c = c.resize((int(c.width*scale), int(c.height*scale)), Image.LANCZOS)
    d = ImageDraw.Draw(c)
    x0,y0 = box[0], box[1]
    ox = x0 - (x0 % step) + step
    while ox < box[2]:
        X = (ox-x0)*scale
        d.line([(X,0),(X,c.height)], fill=(255,0,0), width=1)
        d.text((X+3,3), str(ox), fill=(255,0,0))
        ox += step
    oy = y0 - (y0 % step) + step
    while oy < box[3]:
        Y = (oy-y0)*scale
        d.line([(0,Y),(c.width,Y)], fill=(0,120,255), width=1)
        d.text((3,Y+2), str(oy), fill=(0,120,255))
        oy += step
    p = os.path.join(OUT,'_v8_4_r62_%s.png'%name); c.save(p); print(name, p, c.size)
# NE corner region of photo 96
grid('96',(450,300,1100,1650),'g96_ne',1.4,50)
# SE corner + vent region
grid('96',(2950,900,3900,1600),'g96_se',1.8,50)
# the two small windows top of 96
grid('96',(1100,0,2900,400),'g96_win',1.0,50)
