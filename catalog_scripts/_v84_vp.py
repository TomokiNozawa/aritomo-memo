# -*- coding: utf-8 -*-
import os, math
import numpy as np
from PIL import Image, ImageOps, ImageDraw
BASE = r'C:\Users\t2262\Box\DIK & Company\06_Other\野沢用\claude\nozaROOM\間取り図等'
OUT  = r'C:\Users\t2262\aritomo-memo\catalog_scripts'
p=os.path.join(BASE,'03_キッチン','LINE_ALBUM_20260820 内覧_260820_38.jpg')
im=ImageOps.exif_transpose(Image.open(p)).convert('RGB')
g=np.asarray(im.convert('L'),dtype=np.float32)
print(g.shape)
# horizontal gradient magnitude -> find near-vertical edges: for each row band, find x of local extremes
def edge_x(y, x0, x1):
    row=g[y, x0:x1]
    d=np.abs(np.diff(row))
    i=int(np.argmax(d))
    return x0+i, float(d[i])
# scan candidate vertical seam between drawer columns around x 1600-1800
for y in range(760, 1900, 100):
    print(y, 'colseam', edge_x(y,1560,1800), '| rightend', edge_x(y,3350,3700), '| leftgable', edge_x(y,150,520))
