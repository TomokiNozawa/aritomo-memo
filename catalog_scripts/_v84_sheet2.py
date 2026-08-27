# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps, ImageDraw
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
nums=[('03_キッチン',n) for n in ['74','76','77','78','79','81','83','84','85','29','33','35','40','34']]
nums+= [('02_ダイニング',n) for n in ['31','32']]
cols=4; tw,th=700,540
rows=(len(nums)+cols-1)//cols
sheet=Image.new('RGB',(cols*tw,rows*th),(20,20,20)); d=ImageDraw.Draw(sheet)
for i,(f,n) in enumerate(nums):
    p=os.path.join(BASE,f,'LINE_ALBUM_20260820 内覧_260820_%s.jpg'%n)
    im=ImageOps.exif_transpose(Image.open(p)).convert('RGB'); im.thumbnail((tw-10,th-30))
    x=(i%cols)*tw+5; y=(i//cols)*th+26
    sheet.paste(im,(x,y)); d.text((x+4,y-20),'%s-%s'%(f[:2],n),fill=(255,255,0))
sheet.save(os.path.join(OUT,'_v8_4_kit_sheet2.png'))
print(sheet.size)
