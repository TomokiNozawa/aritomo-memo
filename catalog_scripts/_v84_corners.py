# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageDraw
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
p=os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_38.jpg')
im=ImageOps.exif_transpose(Image.open(p)).convert('RGB')
def zoom(x0,y0,x1,y1,scale,name,gx=25,gy=25):
    c=im.crop((x0,y0,x1,y1)).resize((int((x1-x0)*scale),int((y1-y0)*scale)),Image.LANCZOS)
    d=ImageDraw.Draw(c)
    for ox in range(x0,x1,gx):
        dx=int((ox-x0)*scale); big=(ox%100==0)
        d.line([(dx,0),(dx,c.height)],fill=(255,0,0) if big else (255,150,150),width=1 if not big else 2)
        if big: d.text((dx+2,2),str(ox),fill=(255,0,0))
    for oy in range(y0,y1,gy):
        dy=int((oy-y0)*scale); big=(oy%100==0)
        d.line([(0,dy),(c.width,dy)],fill=(0,120,255) if big else (150,200,255),width=1 if not big else 2)
        if big: d.text((2,dy+2),str(oy),fill=(0,90,255))
    c.save(os.path.join(OUT,name)); print(name,c.size)
zoom(3550,1750,3950,2150,3.0,'_v8_4_kit_m38_botright.png')
zoom(3550,400,3950,800,3.0,'_v8_4_kit_m38_topright.png')
zoom(200,500,600,900,3.0,'_v8_4_kit_m38_topleft.png')
zoom(200,1850,600,2250,3.0,'_v8_4_kit_m38_botleft2.png')
