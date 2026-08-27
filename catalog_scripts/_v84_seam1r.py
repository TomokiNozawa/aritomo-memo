# -*- coding: utf-8 -*-
import os
import numpy as np
from PIL import Image, ImageOps
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
im=ImageOps.exif_transpose(Image.open(os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_38.jpg'))).convert('RGB')
g=np.asarray(im.convert('L'),dtype=np.float32); H,W=g.shape
def prof(x, y0,y1):
    col=g[y0:y1,x]
    d=np.diff(col)
    idx=np.argsort(-np.abs(d))[:6]
    return [(y0+int(i)+0.5, round(float(d[i]),1)) for i in sorted(idx)]
for x in [400,1000,1500,1900,2100,2500,2900,3200,3450,3600,3750]:
    print(x, prof(x,1020,1220))
