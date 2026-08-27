# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageDraw
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
p=os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_38.jpg')
im=ImageOps.exif_transpose(Image.open(p)).convert('RGB')
def strip(x0,x1,y0,y1,scale,name,step=20):
    c=im.crop((x0,y0,x1,y1)); c=c.resize((int((x1-x0)*scale),int((y1-y0)*scale)),Image.LANCZOS)
    d=ImageDraw.Draw(c)
    for oy in range(y0,y1,step):
        dy=int((oy-y0)*scale); big=(oy%100==0)
        d.line([(0,dy),(70 if big else 25,dy)],fill=(255,0,0),width=2)
        if big: d.text((74,dy-9),str(oy),fill=(255,0,0))
    for ox in range(x0,x1,50):
        dx=int((ox-x0)*scale); big=(ox%200==0)
        d.line([(dx,0),(dx,60 if big else 20)],fill=(0,160,255),width=2)
        if big: d.text((dx+3,62),str(ox),fill=(0,160,255))
    c.save(os.path.join(OUT,name)); print(name,c.size)
strip(0,520,1550,2250,2.6,'_v8_4_kit_m38_botleft.png',20)
