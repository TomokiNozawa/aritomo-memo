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
def grid(tag, box, name, scale, step, boost=1.0):
    im = load(tag); c = im.crop(box).convert('RGB')
    if boost!=1.0:
        from PIL import ImageEnhance
        c = ImageEnhance.Contrast(c).enhance(boost)
    c = c.resize((int(c.width*scale), int(c.height*scale)), Image.LANCZOS)
    d = ImageDraw.Draw(c); x0,y0 = box[0], box[1]
    ox = x0 - (x0 % step) + step
    while ox < box[2]:
        X=(ox-x0)*scale; d.line([(X,0),(X,c.height)], fill=(255,0,0)); d.text((X+2,2), str(ox), fill=(255,0,0)); ox+=step
    oy = y0 - (y0 % step) + step
    while oy < box[3]:
        Y=(oy-y0)*scale; d.line([(0,Y),(c.width,Y)], fill=(0,120,255)); d.text((2,Y+2), str(oy), fill=(0,120,255)); oy+=step
    p=os.path.join(OUT,'_v8_4_r62_%s.png'%name); c.save(p); print(name,p,c.size)
grid('96',(600,900,800,1600),'g96_necorner',5.0,20,2.0)
grid('96',(3400,900,3620,1560),'g96_secorner',5.0,20,2.0)
grid('96',(3050,1060,3420,1340),'g96_ventzoom',4.0,20,1.3)
