# -*- coding: utf-8 -*-
import os, io, glob
from PIL import Image, ImageOps, ImageDraw

BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'

folders = {'KIT':'03_キッチン','DIN':'02_ダイニング','LIV':'01_リビング'}

items=[]
for tag,f in folders.items():
    for p in sorted(glob.glob(os.path.join(BASE,f,'*.jpg'))):
        num = os.path.basename(p).split('_')[-1].split('.')[0]
        items.append((tag,num,p))

print("count",len(items))
# per-folder contact sheet
for tag,f in folders.items():
    sub=[it for it in items if it[0]==tag]
    if not sub: continue
    cols=4; tw,th=460,345
    rows=(len(sub)+cols-1)//cols
    sheet=Image.new('RGB',(cols*tw,rows*th),(20,20,20))
    d=ImageDraw.Draw(sheet)
    for i,(t,n,p) in enumerate(sub):
        im=ImageOps.exif_transpose(Image.open(p)).convert('RGB')
        im.thumbnail((tw-8,th-28))
        x=(i%cols)*tw+4; y=(i//cols)*th+24
        sheet.paste(im,(x,y))
        d.text((x+4,y-18),"%s-%s  %dx%d"%(t,n,im.width,im.height),fill=(255,255,0))
    sheet.save(os.path.join(OUT,'_v8_4_kit_sheet_%s.png'%tag))
    print('sheet',tag,sheet.size,len(sub))
