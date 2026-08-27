# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageOps
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
for f,n in [('03_キッチン','76'),('03_キッチン','77'),('03_キッチン','78'),('03_キッチン','79'),
            ('03_キッチン','81'),('03_キッチン','82'),('03_キッチン','83'),('03_キッチン','84'),('03_キッチン','85'),
            ('03_キッチン','74'),('03_キッチン','75'),('03_キッチン','29'),('03_キッチン','33'),('03_キッチン','35'),('03_キッチン','40'),
            ('02_ダイニング','31'),('02_ダイニング','32')]:
    p=os.path.join(BASE,f,'LINE_ALBUM_20260820 内覧_260820_%s.jpg'%n)
    im=ImageOps.exif_transpose(Image.open(p)).convert('RGB')
    im.thumbnail((1300,1300))
    im.save(os.path.join(OUT,'_v8_4_kit_full_%s.png'%n))
print('ok')
